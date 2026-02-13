from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any
from urllib.parse import quote

import httpx

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

    Maintains a per-domain cookie jar (spsc/spid anti-bot cookies) and
    user token obtained via SMS auth. Uses browser-like headers required
    by the booking subdomain API.
    """

    def __init__(self, partner_token: str) -> None:
        self.partner_token = partner_token
        # per-domain: httpx.AsyncClient with cookie jar
        self._sessions: dict[str, httpx.AsyncClient] = {}
        # per-domain: user token obtained after SMS auth
        self._user_tokens: dict[str, str] = {}

    def _get_session(self, domain: str) -> httpx.AsyncClient:
        if domain not in self._sessions:
            self._sessions[domain] = httpx.AsyncClient(
                base_url=f"https://{domain}",
                headers=_BROWSER_HEADERS,
                follow_redirects=True,
                timeout=httpx.Timeout(30.0),
            )
        return self._sessions[domain]

    def _auth_header(self, domain: str) -> str:
        user_token = self._user_tokens.get(domain, "")
        if user_token:
            return f"Bearer {self.partner_token}, User {user_token}"
        return f"Bearer {self.partner_token}"

    def _headers(self, domain: str) -> dict[str, str]:
        return {
            "Accept": "application/vnd.yclients.v2+json",
            "Content-Type": "application/json",
            "Authorization": self._auth_header(domain),
            "Origin": f"https://{domain}",
            "Referer": f"https://{domain}/",
        }

    async def _request(
        self,
        domain: str,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session = self._get_session(domain)
        try:
            response = await session.request(
                method=method,
                url=path,
                headers=self._headers(domain),
                params=params,
                json=json,
            )
        except httpx.TimeoutException:
            return {"error": True, "message": "Request timed out"}
        except httpx.ConnectError as exc:
            return {"error": True, "message": f"Connection failed: {exc}"}

        try:
            return response.json()  # type: ignore[no-any-return]
        except (ValueError, TypeError):
            return {"data": response.text[:2000]}

    # ── Company discovery ─────────────────────────────────────────────────

    async def search_companies(
        self,
        query: str,
        *,
        city_id: int | None = None,
        count: int = 10,
    ) -> dict[str, Any]:
        """Search YCLIENTS companies by name. Returns companies with booking domain info."""
        params: dict[str, Any] = {"q": query, "count": count}
        if city_id:
            params["city_id"] = city_id

        result = await self._request(
            "api.yclients.com", "GET", "/api/v1/companies/", params=params
        )
        # Enrich with booking domain derived from main_group_id
        for company in result.get("data") or []:
            group_id = company.get("main_group_id")
            if group_id:
                company["booking_domain"] = f"n{group_id}.yclients.com"
                company["booking_url"] = f"https://n{group_id}.yclients.com/company/{company['id']}"
        return result

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
        """Send SMS confirmation code to the given phone number."""
        return await self._request(
            domain, "POST", f"/api/v1/book_code/{company_id}",
            json={"phone": phone},
        )

    async def verify_sms_code(
        self, domain: str, company_id: int, phone: str, code: str
    ) -> dict[str, Any]:
        """Verify SMS code and store the user token for subsequent calls."""
        result = await self._request(
            domain, "POST", "/api/v1/user/auth",
            json={"phone": phone, "code": code, "company_id": company_id},
        )
        user_token = (result.get("data") or {}).get("user_token")
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
    ) -> dict[str, Any]:
        """Return the authenticated user's booking history."""
        if chain_id:
            q: dict[str, Any] = {"filter[chain_id]": chain_id}
        else:
            q = {"filter[location_ids][]": company_id}
        if sort_by_nearest:
            q["filter[sort_by_nearest_time]"] = "true"
        return await self._request(domain, "GET", "/api/v1/booking/attendances", params=q)

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

    async def close(self) -> None:
        for client in self._sessions.values():
            await client.aclose()
        self._sessions.clear()
