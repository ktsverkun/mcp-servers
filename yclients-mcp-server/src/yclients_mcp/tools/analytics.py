"""YCLIENTS MCP tools: Analytics — company analytics and Z-reports"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "get_reports_z_report": ("GET", "/api/v1/reports/z_report/{company_id}", True),
    "get_analytics_overall": ("GET", "/api/v1/company/{company_id}/analytics/overall/", True),
    "get_charts_income_daily": (
        "GET",
        "/api/v1/company/{company_id}/analytics/overall/charts/income_daily/",
        True,
    ),
    "get_charts_records_daily": (
        "GET",
        "/api/v1/company/{company_id}/analytics/overall/charts/records_daily/",
        True,
    ),
    "get_charts_fullness_daily": (
        "GET",
        "/api/v1/company/{company_id}/analytics/overall/charts/fullness_daily/",
        True,
    ),
    "get_charts_record_source": (
        "GET",
        "/api/v1/company/{company_id}/analytics/overall/charts/record_source/",
        True,
    ),
    "get_charts_record_status": (
        "GET",
        "/api/v1/company/{company_id}/analytics/overall/charts/record_status/",
        True,
    ),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_analytics(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Analytics — company analytics and Z-reports

        Available operations:
          - get_reports_z_report: [GET] Получить данные Z-Отчета
          - get_analytics_overall: [GET] Получить основные показатели компании
          - get_charts_income_daily: [GET] Получить данные о выручке в разрезе по дням
          - get_charts_records_daily: [GET] Получить данные о количестве записей в разрезе по дням
          - get_charts_fullness_daily: [GET] Получить данные о заполненности в разрезе по дням
          - get_charts_record_source: [GET] Получить структуру записей по источникам
          - get_charts_record_status: [GET] Получить структуру записей по статусам визитов

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
