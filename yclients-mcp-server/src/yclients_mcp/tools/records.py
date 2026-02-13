"""YCLIENTS MCP tools: Records & Visits — manage appointment records and visit history"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "list_records": ("GET", "/api/v1/records/{company_id}", True),
    "create_records": ("POST", "/api/v1/records/{company_id}", True),
    "list_records_partner": ("GET", "/api/v1/records/partner/", True),
    "get_record": ("GET", "/api/v1/record/{company_id}/{record_id}", True),
    "update_record": ("PUT", "/api/v1/record/{company_id}/{record_id}", True),
    "delete_record": ("DELETE", "/api/v1/record/{company_id}/{record_id}", True),
    "get_visits": ("GET", "/api/v1/visits/{visit_id}", True),
    "get_visit_details": ("GET", "/api/v1/visit/details/{salon_id}/{record_id}/{visit_id}", True),
    "update_visits": ("PUT", "/api/v1/visits/{visit_id}/{record_id}", True),
    "get_attendance_receipt_print": ("GET", "/api/v1/attendance/receipt_print/{visit_id}", True),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_records(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Records & Visits — manage appointment records and visit history

        Available operations:
          - list_records: [GET] Получить список записей
          - create_records: [POST] Создать новую запись
          - list_records_partner: [GET] Получить список записей партнёра
          - get_record: [GET] Получить запись
          - update_record: [PUT] Изменить запись
          - delete_record: [DELETE] Удалить запись
          - get_visits: [GET] Получить визит
          - get_visit_details: [GET] Получить детали визита
          - update_visits: [PUT] Изменить визит
          - get_attendance_receipt_print: [GET] Чек PDF по визиту

        Args:
            operation: One of the operation names listed above.
            params: Dict with keys depending on the operation:
                - Path parameters (e.g. company_id, record_id) — used to fill URL placeholders.
                - "query" — dict of query-string parameters.
                - "body" — dict for the JSON request body (POST/PUT/PATCH).
        """
        if operation not in OPERATIONS:
            return {
                "error": True,
                "message": f"Unknown operation '{operation}'. Available: {', '.join(sorted(OPERATIONS))}",
            }

        method, path_template, needs_user = OPERATIONS[operation]
        p = params or {}

        try:
            path = _build_path(path_template, p)
        except ValueError as exc:
            return {"error": True, "message": f"Missing required path parameter: {exc}"}

        return await client.request(
            method=method,
            path=path,
            needs_user_token=needs_user,
            query=p.get("query"),
            body=p.get("body"),
        )
