from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any
from urllib.parse import quote

_PARTNER_TOKEN_PATTERNS = [
    # Angular environment: apiToken:"Bearer <token>" (found in chunk-MJ6XN4MG.js style)
    re.compile(r'apiToken\s*:\s*"Bearer\s+([a-zA-Z0-9_\-]{8,})"'),
    # Generic Bearer token in JS
    re.compile(r'"Bearer\s+([a-zA-Z0-9_\-]{8,})"'),
    # Classic partner_token patterns (hex 32+)
    re.compile(r'"partner_token"\s*:\s*"([a-zA-Z0-9_\-]{8,})"'),
    re.compile(r"'partner_token'\s*:\s*'([a-zA-Z0-9_\-]{8,})'"),
    re.compile(r'partnerToken["\'\s:=]+([a-zA-Z0-9_\-]{8,})'),
    re.compile(r'PARTNER_TOKEN["\'\s:=]+([a-zA-Z0-9_\-]{8,})'),
]

_APP_CONFIG_PATTERNS = {
    "name": re.compile(r'(?:^|[,{])\s*name\s*:\s*"(client\.[a-z]+)"'),
    "version": re.compile(r'(?:^|[,{])\s*version\s*:\s*"([0-9a-f]+\.[0-9a-f]+)"'),
    "brandDomain": re.compile(r'brandDomain\s*:\s*"([a-z]+)"'),
}

import httpx
from curl_cffi.requests import AsyncSession as CurlAsyncSession

from .auth import build_headers
from .config import YClientsConfig

log = logging.getLogger("yclients_mcp")


class RateLimiter:
    """Token-bucket rate limiter: max *per_sec* requests per second."""

    def __init__(self, per_sec: int = 5) -> None:
        self._per_sec = per_sec
        self._tokens = float(per_sec)
        self._last = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._tokens = min(self._per_sec, self._tokens + elapsed * self._per_sec)
            self._last = now
            if self._tokens < 1:
                wait = (1 - self._tokens) / self._per_sec
                await asyncio.sleep(wait)
                self._tokens = 0
            else:
                self._tokens -= 1


def _build_path(template: str, params: dict[str, Any]) -> str:
    """Fill ``{placeholders}`` in *template* from *params*, URL-encoding values.

    Returns the resolved path.
    Raises ``ValueError`` if a required placeholder is missing.
    """
    placeholders = re.findall(r"\{(\w+)\}", template)
    path = template
    for ph in placeholders:
        val = params.get(ph)
        if val is None:
            raise ValueError(ph)
        path = path.replace("{" + ph + "}", quote(str(val), safe=""))
    return path


class YClientsClient:
    """Async HTTP client for the YCLIENTS REST API with rate-limiting."""

    def __init__(self, config: YClientsConfig) -> None:
        self.config = config
        self._limiter = RateLimiter(per_sec=5)
        self._http = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=httpx.Timeout(30.0),
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        needs_user_token: bool = True,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self._limiter.acquire()
        headers = build_headers(self.config, needs_user_token=needs_user_token)

        log.debug("%s %s query=%s", method, path, query)

        try:
            response = await self._http.request(
                method=method,
                url=path,
                headers=headers,
                params=query,
                json=body,
            )
        except httpx.TimeoutException:
            return {"error": True, "status_code": 0, "message": "Request timed out"}
        except httpx.ConnectError as exc:
            return {"error": True, "status_code": 0, "message": f"Connection failed: {exc}"}

        # Retry once on 429 (rate-limited)
        if response.status_code == 429:
            log.warning("Rate-limited (429), retrying in 2 s …")
            await asyncio.sleep(2)
            await self._limiter.acquire()
            try:
                response = await self._http.request(
                    method=method,
                    url=path,
                    headers=headers,
                    params=query,
                    json=body,
                )
            except httpx.HTTPError as exc:
                return {"error": True, "status_code": 0, "message": str(exc)}

        if response.status_code >= 400:
            try:
                detail = response.json()
            except (ValueError, TypeError):
                detail = {"status": response.status_code}
            return {
                "error": True,
                "status_code": response.status_code,
                "detail": detail,
            }

        try:
            return response.json()  # type: ignore[no-any-return]
        except (ValueError, TypeError):
            return {"data": response.text[:2000]}

    async def close(self) -> None:
        await self._http.aclose()


_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "cors",
}


class BookingClient:
    """HTTP client for company-specific booking subdomains (e.g. n864017.yclients.com).

    Uses curl-cffi with Chrome TLS impersonation to bypass JA3 fingerprint
    detection that would otherwise silently block SMS delivery.
    Maintains a per-domain session with cookie jar (spsc/spid anti-bot cookies)
    and user token obtained via SMS auth.
    """

    def __init__(self, partner_token: str) -> None:
        self.partner_token = partner_token
        # per-domain: curl-cffi async session with cookie jar + Chrome TLS
        self._sessions: dict[str, CurlAsyncSession] = {}
        # per-domain: user token obtained after SMS auth
        self._user_tokens: dict[str, str] = {}
        # per-domain: partner token extracted from booking page
        self._partner_tokens: dict[str, str] = {}
        # per-domain: app config extracted from JS (brandDomain, name, version)
        self._app_configs: dict[str, dict[str, str]] = {}

    def _get_session(self, domain: str) -> CurlAsyncSession:
        if domain not in self._sessions:
            self._sessions[domain] = CurlAsyncSession(
                headers=_BROWSER_HEADERS,
                impersonate="chrome120",
                timeout=30,
            )
        return self._sessions[domain]

    def _url(self, domain: str, path: str) -> str:
        """Build full URL from domain and path."""
        if path.startswith("http"):
            return path
        return f"https://{domain}{path}"

    def _resolve_partner_token(self, domain: str) -> str:
        """Return the best available partner token for *domain*.

        Priority:
        1. Token extracted from the company's booking page (per-domain).
        2. Token configured via YCLIENTS_PARTNER_TOKEN env-var.
        """
        return self._partner_tokens.get(domain) or self.partner_token

    def _auth_header(self, domain: str) -> str:
        token = self._resolve_partner_token(domain)
        user_token = self._user_tokens.get(domain, "")
        if not token:
            # No partner token at all — omit Authorization to avoid illegal header
            return ""
        if user_token:
            return f"Bearer {token}, User {user_token}"
        return f"Bearer {token}"

    async def _ensure_partner_token(self, domain: str, company_id: int | None = None) -> None:
        """Lazily fetch and cache the partner token embedded in the booking widget JS.

        Strategy:
        1. Fetch the HTML booking page to get the main JS bundle filename.
           Uses ``/company/{company_id}`` if available (root ``/`` returns 403).
        2. Fetch ``main-*.js`` and collect all chunk names.
        3. Scan JS chunks (incl. transitive imports) for the Angular environment
           object that contains ``apiToken:"Bearer <token>"``.

        The token is extracted once per domain and cached.
        """
        if domain in self._partner_tokens:
            return
        if domain == "api.yclients.com":
            # For API requests, reuse any available partner token
            if self.partner_token:
                self._partner_tokens[domain] = self.partner_token
                return
            # Try any already-extracted domain token
            if self._partner_tokens:
                self._partner_tokens[domain] = next(iter(self._partner_tokens.values()))
                return
            # Bootstrap: extract token from a known booking page
            bootstrap_domain = "n864017.yclients.com"
            await self._ensure_partner_token(bootstrap_domain, company_id=806724)
            if bootstrap_domain in self._partner_tokens:
                self._partner_tokens[domain] = self._partner_tokens[bootstrap_domain]
            return
        if self.partner_token:
            # Already have a globally-configured token — nothing to fetch.
            self._partner_tokens[domain] = self.partner_token
            return

        session = self._get_session(domain)
        html_headers = {
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": _BROWSER_HEADERS["User-Agent"],
        }

        # Step 1: fetch HTML. Root "/" may return 403; try /company/{id} first.
        html_paths = []
        if company_id:
            html_paths.append(f"/company/{company_id}")
        html_paths.append("/")

        html = ""
        for html_path in html_paths:
            try:
                resp = await session.get(self._url(domain, html_path), headers=html_headers)
                if resp.status_code == 200:
                    html = resp.text
                    break
            except Exception as exc:
                log.warning("BookingClient: could not fetch %s%s: %s", domain, html_path, exc)

        if not html:
            log.warning("BookingClient: could not load any booking HTML page for %s", domain)
            return

        # Try patterns on the HTML itself first (older widget versions)
        for pattern in _PARTNER_TOKEN_PATTERNS:
            m = pattern.search(html)
            if m:
                token = m.group(1)
                self._partner_tokens[domain] = token
                log.info("BookingClient: extracted partner_token from HTML for %s (%s…)", domain, token[:8])
                return

        # Step 2: find main-*.js from HTML and extract all chunk names
        main_js_match = re.search(r'src="(main-[^"]+\.js)"', html)
        if not main_js_match:
            log.warning("BookingClient: main-*.js not found in HTML for %s", domain)
            return

        main_js_path = "/" + main_js_match.group(1)
        try:
            resp = await session.get(self._url(domain, main_js_path), headers={"Accept": "*/*", "User-Agent": _BROWSER_HEADERS["User-Agent"]})
            main_js = resp.text
        except Exception as exc:
            log.warning("BookingClient: could not fetch %s: %s", main_js_path, exc)
            return

        # Try patterns in main.js
        for pattern in _PARTNER_TOKEN_PATTERNS:
            m = pattern.search(main_js)
            if m:
                token = m.group(1)
                self._partner_tokens[domain] = token
                log.info("BookingClient: extracted partner_token from main.js for %s (%s…)", domain, token[:8])
                return

        # Step 3: collect all chunk filenames — from HTML modulepreload + main.js imports
        # The token lives in a transitively-imported chunk (e.g. chunk-MJ6XN4MG.js),
        # so we need to follow one level of imports.
        _CHUNK_RE = re.compile(r'["\'./]+(chunk-[A-Z0-9]+\.js)["\']')

        chunks_from_html: list[str] = re.findall(r'href="(chunk-[^"]+\.js)"', html)
        chunks_from_main: list[str] = _CHUNK_RE.findall(main_js)
        all_chunks = list(dict.fromkeys(chunks_from_html + chunks_from_main))  # deduplicate
        log.debug("BookingClient: scanning %d chunks for %s", len(all_chunks), domain)

        js_headers = {"Accept": "*/*", "User-Agent": _BROWSER_HEADERS["User-Agent"]}
        seen_transitive: set[str] = set()

        async def scan_chunk(chunk_path: str) -> str | None:
            try:
                r = await session.get(self._url(domain, "/" + chunk_path), headers=js_headers)
                js = r.text
            except Exception:
                return None
            for pat in _PARTNER_TOKEN_PATTERNS:
                mt = pat.search(js)
                if mt:
                    # Also extract app config from this same chunk (env object)
                    if domain not in self._app_configs:
                        cfg: dict[str, str] = {}
                        for key, cpat in _APP_CONFIG_PATTERNS.items():
                            cm = cpat.search(js)
                            if cm:
                                cfg[key] = cm.group(1)
                        if cfg:
                            self._app_configs[domain] = cfg
                            log.debug("BookingClient: extracted app config for %s: %s", domain, cfg)
                    return mt.group(1)
            # Collect transitive imports from this chunk (one level deep)
            for imp in _CHUNK_RE.findall(js):
                seen_transitive.add(imp)
            return None

        for chunk_path in all_chunks:
            result = await scan_chunk(chunk_path)
            if result:
                self._partner_tokens[domain] = result
                log.info("BookingClient: extracted partner_token from %s for %s (%s…)", chunk_path, domain, result[:8])
                return

        # Step 4: scan transitive imports not yet checked
        for chunk_path in seen_transitive - set(all_chunks):
            result = await scan_chunk(chunk_path)
            if result:
                self._partner_tokens[domain] = result
                log.info("BookingClient: extracted partner_token from transitive %s for %s (%s…)", chunk_path, domain, result[:8])
                return

        log.warning("BookingClient: partner_token not found in any JS for %s", domain)

    def _headers(self, domain: str) -> dict[str, str]:
        h: dict[str, str] = {
            # Angular HttpClient default — matches what the real booking widget sends
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": f"https://{domain}",
            "Referer": f"https://{domain}/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        auth = self._auth_header(domain)
        if auth:
            h["Authorization"] = auth
        # Add X-{brandDomain}-Application-* headers if we have the app config
        cfg = self._app_configs.get(domain)
        if cfg:
            brand = cfg.get("brandDomain", "yclients")
            h[f"X-{brand}-Application-Name"] = cfg.get("name", "client.booking")
            h[f"X-{brand}-Application-Platform"] = "angular-18.2.13"
            h[f"X-{brand}-Application-Version"] = cfg.get("version", "")
            # Empty security headers — required only for book_record/attendances with reCAPTCHA
            h["X-App-Validation-Token"] = ""
            h["X-App-Signature"] = ""
        return h

    async def _request(
        self,
        domain: str,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        # Try to extract a company_id hint from the API path (e.g. /api/v1/book_code/806724)
        _cid_match = re.search(r"/(\d{4,})", path)
        _company_id_hint = int(_cid_match.group(1)) if _cid_match else None
        await self._ensure_partner_token(domain, company_id=_company_id_hint)
        session = self._get_session(domain)
        headers = {**self._headers(domain), **(extra_headers or {})}
        try:
            response = await session.request(
                method=method,
                url=self._url(domain, path),
                headers=headers,
                params=params,
                json=json,
            )
        except Exception as exc:
            err = str(exc)
            if "timed out" in err.lower() or "timeout" in err.lower():
                return {"error": True, "message": "Request timed out"}
            return {"error": True, "message": f"Connection failed: {err}"}

        try:
            data: dict[str, Any] = response.json()
        except (ValueError, TypeError):
            data = {"data": response.text[:2000]}

        if response.status_code >= 400:
            if isinstance(data, dict):
                data["_status_code"] = response.status_code
            else:
                data = {"error": True, "_status_code": response.status_code}

        # Capture X-App-Security-Level header (contains recaptcha_v3 key on 412)
        security_header = response.headers.get("X-App-Security-Level")
        if security_header and isinstance(data, dict):
            try:
                import json as _json
                data["_security_level"] = _json.loads(security_header)
            except (ValueError, TypeError):
                pass

        return data

    # ── Company discovery ─────────────────────────────────────────────────

    # Common business_type_ids for parallel scanning when no type specified
    _COMMON_BUSINESS_TYPES = [10, 1, 18, 32, 2, 48, 3, 35]
    # 10=fitness, 1=salon, 18=barbershop, 32=cosmetics, 2=medical,
    # 48=studio, 3=sport, 35=spa

    async def search_companies(
        self,
        query: str,
        *,
        city_id: int | None = None,
        group_id: int | None = None,
        business_type_id: int | None = None,
        count: int = 10,
    ) -> dict[str, Any]:
        """Search YCLIENTS companies by name (client-side text filter).

        The YCLIENTS REST API ``GET /api/v1/companies/`` does NOT support
        text search — any ``title``/``q`` parameter is silently ignored.
        We work around this by fetching pages of companies (with optional
        ``city_id`` / ``business_type_id`` / ``group_id`` filters) and
        matching *query* against the ``title`` field locally.

        When neither ``group_id`` nor ``business_type_id`` is given, we
        scan several common business types in parallel for speed.
        """
        query_lower = query.lower()

        if group_id or business_type_id:
            # Specific filter — single paginated scan
            return await self._search_companies_paginated(
                query_lower, city_id=city_id, group_id=group_id,
                business_type_id=business_type_id, count=count,
            )

        # No type filter — scan common business types in parallel (shallow)
        tasks = [
            self._search_companies_paginated(
                query_lower, city_id=city_id, business_type_id=bt, count=count,
                max_pages=3,
            )
            for bt in self._COMMON_BUSINESS_TYPES
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        seen_ids: set[int] = set()
        matched: list[dict[str, Any]] = []
        for r in results:
            if isinstance(r, Exception):
                continue
            for company in r.get("data", []):
                cid = company.get("id")
                if cid and cid not in seen_ids:
                    seen_ids.add(cid)
                    matched.append(company)

        return {"success": True, "count": len(matched), "data": matched[:count]}

    async def _search_companies_paginated(
        self,
        query_lower: str,
        *,
        city_id: int | None = None,
        group_id: int | None = None,
        business_type_id: int | None = None,
        count: int = 10,
        max_pages: int = 20,
    ) -> dict[str, Any]:
        api_params: dict[str, Any] = {"count": 200}
        if city_id:
            api_params["city_id"] = city_id
        if group_id:
            api_params["group_id"] = group_id
        if business_type_id:
            api_params["business_type_id"] = business_type_id

        matched: list[dict[str, Any]] = []

        for page in range(1, max_pages + 1):
            api_params["page"] = page
            result = await self._request(
                "api.yclients.com", "GET", "/api/v1/companies/", params=api_params
            )
            companies = result if isinstance(result, list) else (result.get("data") or [])
            if not companies:
                break

            for company in companies:
                title = (company.get("title") or "").lower()
                public_title = (company.get("public_title") or "").lower()
                if query_lower in title or query_lower in public_title:
                    mgid = company.get("main_group_id")
                    if mgid:
                        company["booking_domain"] = f"n{mgid}.yclients.com"
                        company["booking_url"] = f"https://n{mgid}.yclients.com/company/{company['id']}"
                    matched.append(company)

            if len(matched) >= count or len(companies) < 200:
                break

        return {"success": True, "count": len(matched), "data": matched[:count]}

    async def get_company_booking_info(self, company_id: int) -> dict[str, Any]:
        """Get company details including its booking domain."""
        result = await self._request(
            "api.yclients.com", "GET", f"/api/v1/company/{company_id}"
        )
        company = result.get("data") or {}
        group_id = company.get("main_group_id")
        if group_id:
            result["booking_domain"] = f"n{group_id}.yclients.com"
            result["booking_url"] = f"https://n{group_id}.yclients.com/company/{company_id}"
        return result

    # ── SMS auth flow ─────────────────────────────────────────────────────

    async def send_sms_code(self, domain: str, company_id: int, phone: str) -> dict[str, Any]:
        """Send SMS confirmation code to the given phone number.

        Mimics the Angular app flow: first call the channel endpoint (GET),
        then request the SMS code (POST). Uses the company page as Referer.
        """
        referer = f"https://{domain}/company/{company_id}"
        extra = {"Referer": referer}

        # Step 1: check channel (as the real booking widget does before sending code)
        channel_resp = await self._request(
            domain, "GET", f"/api/v1/book_code/{company_id}/channel",
            params={"phone": phone},
            extra_headers=extra,
        )
        log.debug("book_code channel response: %s", channel_resp)

        # Step 2: send the SMS code
        return await self._request(
            domain, "POST", f"/api/v1/book_code/{company_id}",
            json={"phone": phone},
            extra_headers=extra,
        )

    async def verify_sms_code(
        self, domain: str, company_id: int, phone: str, code: str
    ) -> dict[str, Any]:
        """Verify SMS code and store the user token for subsequent calls."""
        result = await self._request(
            domain, "POST", "/api/v1/user/auth",
            json={"phone": phone, "code": code, "company_id": company_id},
        )
        user_token = result.get("user_token") or (result.get("data") or {}).get("user_token")
        if user_token:
            self._user_tokens[domain] = user_token
            log.info("BookingClient: user_token stored for domain %s", domain)
        return result

    def set_user_token(self, domain: str, user_token: str) -> None:
        """Manually set a user token (e.g. from previous auth)."""
        self._user_tokens[domain] = user_token

    def get_user_token(self, domain: str) -> str | None:
        return self._user_tokens.get(domain)

    # ── User attendances ──────────────────────────────────────────────────

    async def get_user_attendances(
        self,
        domain: str,
        company_id: int,
        *,
        sort_by_nearest: bool = True,
        chain_id: int | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """Return the authenticated user's booking history (compact format).

        Optional date_from / date_to (YYYY-MM-DD) filter client-side.
        Returns a flat list instead of raw JSON:API.
        """
        if chain_id:
            q: dict[str, Any] = {"filter[chain_id]": chain_id}
        else:
            q = {"filter[location_ids][]": company_id}
        if sort_by_nearest:
            q["filter[sort_by_nearest_time]"] = "true"
        raw = await self._request(domain, "GET", "/api/v1/booking/attendances", params=q)
        return self._parse_attendances(raw, date_from=date_from, date_to=date_to)

    @staticmethod
    def _parse_attendances(
        raw: dict[str, Any],
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        """Transform JSON:API attendances into a compact flat list.

        The API returns a JSON:API structure with nested relationships:
          attendance -> relationships.records -> included record
            -> relationships.attendance_service_items -> included service
            -> relationships.staff -> included staff
        We resolve two levels of nesting to extract service/staff info.
        """
        records = raw.get("data")
        if not isinstance(records, list):
            return raw  # pass through errors as-is

        # Build lookup for included resources (key by (type, str(id)))
        inc_map: dict[tuple[str, str], dict[str, Any]] = {}
        for item in raw.get("included") or []:
            inc_map[(item.get("type", ""), str(item.get("id", "")))] = item

        status_map = {0: "ожидает", 1: "подтверждён", 2: "пришёл", -1: "не пришёл"}
        result = []

        for r in records:
            attrs = r.get("attributes", {})
            dt_str = attrs.get("datetime", "")
            if not dt_str:
                continue

            # Date filtering
            date_part = dt_str[:10]  # "YYYY-MM-DD"
            if date_from and date_part < date_from:
                continue
            if date_to and date_part > date_to:
                continue

            # Resolve nested record -> service_items / staff
            services: list[dict[str, Any]] = []
            staff_name = ""
            staff_specialization = ""

            rels = r.get("relationships", {})
            for rec_ref in rels.get("records", {}).get("data") or []:
                rec = inc_map.get((rec_ref.get("type", ""), str(rec_ref.get("id", ""))))
                if not rec:
                    continue
                rec_rels = rec.get("relationships", {})

                # Service items
                for si_ref in rec_rels.get("attendance_service_items", {}).get("data") or []:
                    si = inc_map.get((si_ref.get("type", ""), str(si_ref.get("id", ""))))
                    if not si:
                        continue
                    si_a = si.get("attributes", {})
                    svc: dict[str, Any] = {"title": si_a.get("title", "")}
                    cost = si_a.get("cost")
                    if cost is not None:
                        svc["cost"] = cost
                    discount = si_a.get("discount")
                    if discount:
                        svc["discount"] = discount
                    price = si_a.get("price_min")
                    if price is not None:
                        svc["price"] = price
                    services.append(svc)

                # Staff
                staff_ref = rec_rels.get("staff", {}).get("data")
                if staff_ref and not staff_name:
                    if isinstance(staff_ref, list):
                        staff_ref = staff_ref[0] if staff_ref else None
                    if staff_ref:
                        stf = inc_map.get((staff_ref.get("type", ""), str(staff_ref.get("id", ""))))
                        if stf:
                            stf_a = stf.get("attributes", {})
                            staff_name = stf_a.get("name", "")
                            staff_specialization = stf_a.get("specialization", "")

            entry: dict[str, Any] = {
                "id": r.get("id"),
                "datetime": dt_str,
                "create_date": attrs.get("create_date", ""),
                "services": services,
                "staff": staff_name,
                "staff_specialization": staff_specialization,
                "status": status_map.get(attrs.get("attendance_status"), str(attrs.get("attendance_status"))),
                "duration_min": (attrs.get("duration") or 0) // 60,
                "paid_amount": attrs.get("paid_amount"),
                "is_prepaid": attrs.get("is_prepaid", False),
                "activity_id": attrs.get("activity_id") or None,
                "comment": attrs.get("comment") or None,
                "is_deleted": attrs.get("is_deleted", False),
                "can_cancel": attrs.get("is_delete_record_allowed", False),
                "can_change": attrs.get("is_change_record_allowed", False),
            }
            result.append(entry)

        return {"success": True, "total": len(result), "records": result}

    # ── Activity schedule ─────────────────────────────────────────────────

    async def search_activities(
        self,
        domain: str,
        company_id: int,
        date: str,
        *,
        staff_id: int | None = None,
        service_id: int | None = None,
    ) -> dict[str, Any]:
        """Search group activities for a given date."""
        q: dict[str, Any] = {"date": date}
        if staff_id:
            q["staff_id"] = staff_id
        if service_id:
            q["service_id"] = service_id
        return await self._request(
            domain, "GET", f"/api/v1/activity/{company_id}/search", params=q
        )

    # ── Book activity ─────────────────────────────────────────────────────

    async def book_activity(
        self,
        domain: str,
        company_id: int,
        activity_id: int,
        *,
        phone: str,
        fullname: str,
        email: str = "",
        comment: str = "",
        abonement: bool = False,
        notify_by_sms: int = 24,
        notify_by_email: int = 24,
        is_personal_data_processing_allowed: bool = True,
    ) -> dict[str, Any]:
        """Book a group activity (CrossFit, yoga, etc.)."""
        return await self._request(
            domain, "POST", f"/api/v1/activity/{company_id}/{activity_id}/book",
            json={
                "phone": phone,
                "fullname": fullname,
                "email": email,
                "comment": comment,
                "abonement": abonement,
                "notify_by_sms": notify_by_sms,
                "notify_by_email": notify_by_email,
                "is_personal_data_processing_allowed": is_personal_data_processing_allowed,
                "is_newsletter_allowed": False,
                "is_yc_newsletter_allowed": False,
                "is_yc_personal_data_processing_allowed": False,
            },
        )

    # ── Regular appointment booking ──────────────────────────────────────

    async def list_services(
        self, domain: str, company_id: int, *, staff_id: int | None = None,
    ) -> dict[str, Any]:
        """List bookable services. Optionally filter by staff_id."""
        params: dict[str, Any] = {}
        if staff_id:
            params["staff_id"] = staff_id
        raw = await self._request(
            domain, "GET", f"/api/v1/book_services/{company_id}", params=params or None,
        )
        # Flatten: API returns nested categories with services inside
        if isinstance(raw, dict) and "services" in raw:
            raw = raw["services"]
        if not isinstance(raw, list):
            return raw  # pass through errors
        flat: list[dict[str, Any]] = []
        for item in raw:
            svcs = item.get("services") if isinstance(item, dict) else None
            if isinstance(svcs, list):
                # category with nested services
                cat = item.get("title", "")
                for s in svcs:
                    s["category"] = cat
                    flat.append(s)
            else:
                flat.append(item)
        compact = []
        for s in flat:
            entry: dict[str, Any] = {
                "id": s.get("id"),
                "title": s.get("title", ""),
            }
            price = s.get("price_min")
            if price is not None:
                entry["price_min"] = price
            price_max = s.get("price_max")
            if price_max is not None and price_max != price:
                entry["price_max"] = price_max
            dur = s.get("seance_length")
            if dur:
                entry["duration_min"] = dur // 60
            cat = s.get("category")
            if cat:
                entry["category"] = cat
            compact.append(entry)
        return {"success": True, "count": len(compact), "services": compact}

    async def list_staff(
        self, domain: str, company_id: int, *, service_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """List bookable staff. Optionally filter by service_ids."""
        params: dict[str, Any] = {}
        if service_ids:
            for sid in service_ids:
                params.setdefault("service_ids[]", [])
            # curl-cffi doesn't handle list params well, build manually
        raw = await self._request(
            domain, "GET", f"/api/v1/book_staff/{company_id}", params=params or None,
        )
        staff_list = raw if isinstance(raw, list) else (raw.get("data") or [])
        compact = []
        for s in staff_list:
            entry: dict[str, Any] = {
                "id": s.get("id"),
                "name": s.get("name", ""),
            }
            spec = s.get("specialization")
            if spec:
                entry["specialization"] = spec
            rating = s.get("rating")
            if rating:
                entry["rating"] = rating
            compact.append(entry)
        return {"success": True, "count": len(compact), "staff": compact}

    async def list_dates(
        self, domain: str, company_id: int,
        *, staff_id: int | None = None,
    ) -> dict[str, Any]:
        """List dates available for booking."""
        params: dict[str, Any] = {}
        if staff_id:
            params["staff_id"] = staff_id
        raw = await self._request(
            domain, "GET", f"/api/v1/book_dates/{company_id}", params=params or None,
        )
        if isinstance(raw, dict):
            return {
                "success": True,
                "working_dates": raw.get("working_dates", []),
            }
        return raw

    async def list_times(
        self, domain: str, company_id: int, staff_id: int, date: str,
    ) -> dict[str, Any]:
        """List available time slots for a given staff member on a date."""
        raw = await self._request(
            domain, "GET", f"/api/v1/book_times/{company_id}/{staff_id}/{date}",
        )
        slots = raw if isinstance(raw, list) else (raw.get("data") or [])
        compact = []
        for s in slots:
            compact.append({
                "time": s.get("time", ""),
                "datetime": s.get("datetime", ""),
                "duration_min": (s.get("seance_length") or 0) // 60,
            })
        return {"success": True, "count": len(compact), "slots": compact}

    async def book_record(
        self,
        domain: str,
        company_id: int,
        *,
        staff_id: int,
        service_ids: list[int],
        datetime_str: str,
        phone: str,
        fullname: str,
        email: str = "",
        comment: str = "",
        notify_by_sms: int = 24,
        notify_by_email: int = 24,
        captcha_token: str = "",
    ) -> dict[str, Any]:
        """Create a regular appointment (non-group-activity).

        Parameters:
            datetime_str: ISO datetime, e.g. "2026-02-28T14:30:00+03:00"
            service_ids: list of service IDs to book
            captcha_token: reCAPTCHA v3 token (if available) to pass in X-App-Validation-Token
        """
        appointments = [{
            "id": 1,
            "services": [{"id": sid} for sid in service_ids],
            "staff_id": staff_id,
            "datetime": datetime_str,
        }]
        body: dict[str, Any] = {
            "phone": phone,
            "fullname": fullname,
            "email": email,
            "comment": comment,
            "notify_by_sms": notify_by_sms,
            "notify_by_email": notify_by_email,
            "appointments": appointments,
            "is_personal_data_processing_allowed": True,
            "is_newsletter_allowed": False,
            "is_yc_newsletter_allowed": False,
            "is_yc_personal_data_processing_allowed": False,
        }
        extra_headers: dict[str, str] | None = None
        if captcha_token:
            extra_headers = {"X-App-Validation-Token": captcha_token}

        result = await self._request(
            domain, "POST", f"/api/v1/book_record/{company_id}", json=body,
            extra_headers=extra_headers,
        )

        # 412 = reCAPTCHA or user confirmation required by YCLIENTS
        if result.get("_status_code") == 412:
            # Try to get security info from response header (preferred)
            security = result.get("_security_level") or {}
            # Fallback to JSON body errors
            if not security:
                security = (result.get("errors") or {}).get("X-App-Security-Level") or {}

            recaptcha_v3 = security.get("recaptcha_v3") or {}
            recaptcha_key = recaptcha_v3.get("key", "")
            user_confirm = security.get("user_confirm") or {}
            user_confirm_url = user_confirm.get("url", "")
            user_confirm_token = user_confirm.get("token", "")
            # Also extract token from URL if not directly available
            if not user_confirm_token and user_confirm_url:
                m = re.search(r"/user/confirm/([a-f0-9]{40,})", user_confirm_url)
                if m:
                    user_confirm_token = m.group(1)
            return {
                "error": True,
                "requires_captcha": True,
                "recaptcha_v3_key": recaptcha_key or None,
                "user_confirm_url": user_confirm_url or None,
                "user_confirm_token": user_confirm_token or None,
                "message": (
                    "YCLIENTS requires phone verification for booking."
                    + (f" Call user_confirm_start_check with token: {user_confirm_token}" if user_confirm_token else "")
                    + (f" reCAPTCHA site key: {recaptcha_key}" if recaptcha_key else "")
                ),
            }

        return result

    async def user_confirm_start_check(self, token: str) -> dict[str, Any]:
        """Send SMS to user's phone for booking confirmation (api.yclients.com)."""
        pt = self.partner_token or next(iter(self._partner_tokens.values()), "")
        headers: dict[str, str] = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://yclients.com",
            "Referer": f"https://yclients.com/user/confirm/{token}/",
        }
        if pt:
            headers["Authorization"] = f"Bearer {pt}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"https://api.yclients.com/api/v1/user/confirm/token/{token}/start_check",
                    headers=headers,
                )
            except httpx.TimeoutException:
                return {"error": True, "message": "Request timed out"}
            except httpx.ConnectError as exc:
                return {"error": True, "message": f"Connection failed: {exc}"}
        try:
            data: dict[str, Any] = resp.json()
        except (ValueError, TypeError):
            data = {"data": resp.text[:2000]}
        if resp.status_code >= 400:
            if isinstance(data, dict):
                data["_status_code"] = resp.status_code
            else:
                data = {"error": True, "_status_code": resp.status_code}
        return data

    async def user_confirm_check_captcha(self, token: str, captcha_token: str) -> dict[str, Any]:
        """Submit reCAPTCHA v2 token for booking confirmation (api.yclients.com).

        Call after user_confirm_start_check returns check_captcha='google_recaptcha_v2'.
        Response indicates whether check_code (SMS) is also needed.
        """
        pt = self.partner_token or next(iter(self._partner_tokens.values()), "")
        headers: dict[str, str] = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://yclients.com",
            "Referer": f"https://yclients.com/user/confirm/{token}/",
        }
        if pt:
            headers["Authorization"] = f"Bearer {pt}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"https://api.yclients.com/api/v1/user/confirm/token/{token}/check_captcha",
                    headers=headers,
                    json={"captcha_token": captcha_token},
                )
            except httpx.TimeoutException:
                return {"error": True, "message": "Request timed out"}
            except httpx.ConnectError as exc:
                return {"error": True, "message": f"Connection failed: {exc}"}
        try:
            data3: dict[str, Any] = resp.json()
        except (ValueError, TypeError):
            data3 = {"data": resp.text[:2000]}
        if resp.status_code >= 400:
            if isinstance(data3, dict):
                data3["_status_code"] = resp.status_code
            else:
                data3 = {"error": True, "_status_code": resp.status_code}
        return data3

    async def user_confirm_check_code(self, token: str, code: str) -> dict[str, Any]:
        """Verify SMS code to confirm a pending booking (api.yclients.com)."""
        pt = self.partner_token or next(iter(self._partner_tokens.values()), "")
        headers: dict[str, str] = {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": "https://yclients.com",
            "Referer": f"https://yclients.com/user/confirm/{token}/",
        }
        if pt:
            headers["Authorization"] = f"Bearer {pt}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"https://api.yclients.com/api/v1/user/confirm/token/{token}/check_code",
                    headers=headers,
                    json={"code": code},
                )
            except httpx.TimeoutException:
                return {"error": True, "message": "Request timed out"}
            except httpx.ConnectError as exc:
                return {"error": True, "message": f"Connection failed: {exc}"}
        try:
            data2: dict[str, Any] = resp.json()
        except (ValueError, TypeError):
            data2 = {"data": resp.text[:2000]}
        if resp.status_code >= 400:
            if isinstance(data2, dict):
                data2["_status_code"] = resp.status_code
            else:
                data2 = {"error": True, "_status_code": resp.status_code}
        return data2

    async def close(self) -> None:
        for session in self._sessions.values():
            await session.close()
        self._sessions.clear()
