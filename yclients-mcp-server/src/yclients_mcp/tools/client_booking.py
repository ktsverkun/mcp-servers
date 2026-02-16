"""YCLIENTS MCP tools: Client-side booking via company booking subdomain.

Unlike the other tools that use api.yclients.com, these operations go through
the company's booking subdomain (e.g. n864017.yclients.com) and require
browser-like headers + session cookies.

Discovery flow:
  1. search_companies     — find a salon/gym by name
  2. get_company_booking_info — get company details + booking domain

Auth flow:
  3. send_sms_code   — request SMS code
  4. verify_sms_code — exchange code for user token (stored per domain)

After auth, you can:
  - get_user_attendances — list the user's bookings
  - search_activities    — find group classes by date/trainer
  - book_activity        — sign up for a group class (with optional abonement)
"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import BookingClient


def register(mcp: FastMCP, booking_client: BookingClient) -> None:
    @mcp.tool()
    async def yclients_client_booking(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Client-side booking via company booking subdomain (e.g. n864017.yclients.com).

        Available operations:

          search_companies
            Find salons/gyms/studios by name (client-side text match).
            Returns company list with id, title, address, phone, and booking_domain.
            params: query (str) — name or keyword to search
            optional: city_id (int) — filter by city (2=Moscow, 1=SPb),
              group_id (int) — filter by chain/network,
              business_type_id (int) — filter by type (10=fitness, 1=salon, 18=barbershop),
              count (int, default 10)

          get_company_booking_info
            Get full details for a specific company including its booking_domain.
            params: company_id (int)

        For operations below, **domain** is required — the booking subdomain
        (e.g. "n864017.yclients.com"). Use search_companies or get_company_booking_info
        to discover it automatically.

          send_sms_code
            Request SMS confirmation code.
            params: domain, company_id (int), phone (str, e.g. "79161234567")

          verify_sms_code
            Verify SMS code → stores user token for this domain automatically.
            params: domain, company_id (int), phone (str), code (str)

          get_auth_status
            Check whether a user token is already stored for this domain.
            params: domain

          set_user_token
            Manually set a user token (if you already have one).
            params: domain, user_token (str)

          get_user_attendances
            List the authenticated user's bookings (compact format).
            params: domain, company_id (int)
            optional: chain_id (int) — use instead of company_id for chains,
              date_from (str, "YYYY-MM-DD"), date_to (str, "YYYY-MM-DD") — filter by date range

          search_activities
            Find group classes on a specific date.
            params: domain, company_id (int), date (str, "YYYY-MM-DD")
            optional: staff_id (int), service_id (int)

          book_activity
            Sign up for a group class.
            params: domain, company_id (int), activity_id (int),
                    phone (str), fullname (str)
            optional: email (str), comment (str), abonement (bool, default false),
                      notify_by_sms (int, hours before, default 24),
                      notify_by_email (int, hours before, default 24)
        """
        p = params or {}

        # ── search_companies ──────────────────────────────────────────────
        if operation == "search_companies":
            query = p.get("query", "")
            if not query:
                return {"error": True, "message": "Required param: query"}
            return await booking_client.search_companies(
                query,
                city_id=int(p["city_id"]) if p.get("city_id") else None,
                group_id=int(p["group_id"]) if p.get("group_id") else None,
                business_type_id=int(p["business_type_id"]) if p.get("business_type_id") else None,
                count=int(p.get("count", 10)),
            )

        # ── get_company_booking_info ──────────────────────────────────────
        elif operation == "get_company_booking_info":
            company_id = p.get("company_id")
            if not company_id:
                return {"error": True, "message": "Required param: company_id"}
            return await booking_client.get_company_booking_info(int(company_id))

        domain: str = p.get("domain", "")
        if not domain:
            return {"error": True, "message": "Required param: domain (e.g. 'n864017.yclients.com'). Use search_companies to find it."}

        # ── send_sms_code ─────────────────────────────────────────────────
        if operation == "send_sms_code":
            company_id = p.get("company_id")
            phone = p.get("phone", "")
            if not company_id or not phone:
                return {"error": True, "message": "Required params: company_id, phone"}
            return await booking_client.send_sms_code(domain, int(company_id), phone)

        # ── verify_sms_code ───────────────────────────────────────────────
        elif operation == "verify_sms_code":
            company_id = p.get("company_id")
            phone = p.get("phone", "")
            code = p.get("code", "")
            if not company_id or not phone or not code:
                return {"error": True, "message": "Required params: company_id, phone, code"}
            result = await booking_client.verify_sms_code(domain, int(company_id), phone, code)
            # Annotate whether token was saved
            stored = booking_client.get_user_token(domain)
            result["_user_token_stored"] = bool(stored)
            return result

        # ── get_auth_status ───────────────────────────────────────────────
        elif operation == "get_auth_status":
            token = booking_client.get_user_token(domain)
            return {
                "domain": domain,
                "authenticated": bool(token),
                "user_token": token or None,
            }

        # ── set_user_token ────────────────────────────────────────────────
        elif operation == "set_user_token":
            user_token = p.get("user_token", "")
            if not user_token:
                return {"error": True, "message": "Required param: user_token"}
            booking_client.set_user_token(domain, user_token)
            return {"success": True, "message": f"User token set for domain {domain}"}

        # ── get_user_attendances ──────────────────────────────────────────
        elif operation == "get_user_attendances":
            company_id = p.get("company_id")
            if not company_id:
                return {"error": True, "message": "Required param: company_id"}
            chain_id = p.get("chain_id")
            return await booking_client.get_user_attendances(
                domain, int(company_id),
                chain_id=int(chain_id) if chain_id else None,
                date_from=p.get("date_from"),
                date_to=p.get("date_to"),
            )

        # ── search_activities ─────────────────────────────────────────────
        elif operation == "search_activities":
            company_id = p.get("company_id")
            date = p.get("date", "")
            if not company_id or not date:
                return {"error": True, "message": "Required params: company_id, date (YYYY-MM-DD)"}
            return await booking_client.search_activities(
                domain, int(company_id), date,
                staff_id=int(p["staff_id"]) if p.get("staff_id") else None,
                service_id=int(p["service_id"]) if p.get("service_id") else None,
            )

        # ── book_activity ─────────────────────────────────────────────────
        elif operation == "book_activity":
            company_id = p.get("company_id")
            activity_id = p.get("activity_id")
            phone = p.get("phone", "")
            fullname = p.get("fullname", "")
            if not company_id or not activity_id or not phone or not fullname:
                return {"error": True, "message": "Required params: company_id, activity_id, phone, fullname"}
            return await booking_client.book_activity(
                domain, int(company_id), int(activity_id),
                phone=phone,
                fullname=fullname,
                email=p.get("email", ""),
                comment=p.get("comment", ""),
                abonement=bool(p.get("abonement", False)),
                notify_by_sms=int(p.get("notify_by_sms", 24)),
                notify_by_email=int(p.get("notify_by_email", 24)),
                is_personal_data_processing_allowed=bool(
                    p.get("is_personal_data_processing_allowed", True)
                ),
            )

        else:
            available = [
                "search_companies", "get_company_booking_info",
                "send_sms_code", "verify_sms_code", "get_auth_status",
                "set_user_token", "get_user_attendances",
                "search_activities", "book_activity",
            ]
            return {"error": True, "message": f"Unknown operation '{operation}'. Available: {available}"}
