"""YCLIENTS MCP tools: Group Events — create, update, delete group events and sessions"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "create_activity": ("POST", "/api/v1/activity/{company_id}", True),
    "get_activity": ("GET", "/api/v1/activity/{company_id}/{activity_id}", True),
    "update_activity": ("PUT", "/api/v1/activity/{company_id}/{activity_id}", True),
    "delete_activity": ("DELETE", "/api/v1/activity/{company_id}/{activity_id}", True),
    "get_activity_filters": ("GET", "/api/v1/activity/{company_id}/filters/", False),
    "get_activity_search_dates_range": (
        "GET",
        "/api/v1/activity/{company_id}/search_dates_range/",
        False,
    ),
    "get_activity_search_dates": ("GET", "/api/v1/activity/{company_id}/search_dates/", False),
    "get_activity_search": ("GET", "/api/v1/activity/{company_id}/search/", False),
    "get_activity_services_staff_id_1_term_test": (
        "GET",
        "/api/v1/activity/{company_id}/services?staff_id=1&term=test",
        True,
    ),
    "get_activity_duplication_strategy": (
        "GET",
        "/api/v1/activity/{company_id}/duplication_strategy",
        True,
    ),
    "create_activity_duplication_strategy": (
        "POST",
        "/api/v1/activity/{company_id}/duplication_strategy",
        True,
    ),
    "create_activity_duplication_strategy_2": (
        "POST",
        "/api/v1/activity/{company_id}/duplication_strategy/{strategy_id}",
        True,
    ),
    "create_activity_duplicate": (
        "POST",
        "/api/v1/activity/{company_id}/{activity_id}/duplicate/",
        True,
    ),
    "create_companies_activities": ("POST", "/api/v2/companies/{salonId}/activities", True),
    "get_companies_activities": (
        "GET",
        "/api/v2/companies/{salonId}/activities/{activityId}",
        True,
    ),
    "update_companies_activities": (
        "PUT",
        "/api/v2/companies/{salonId}/activities/{activityId}",
        True,
    ),
    "delete_companies_activities": (
        "DELETE",
        "/api/v2/companies/{salonId}/activities/{activityId}",
        True,
    ),
    "create_activities_records": (
        "POST",
        "/api/v2/companies/{salonId}/activities/{activityId}/records",
        True,
    ),
    "create_activities_records_2": (
        "POST",
        "/api/v2/companies/{salonId}/activities/{activityId}/records/{recordId}",
        True,
    ),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_group_events(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Group Events — create, update, delete group events and sessions

        Available operations:
          - create_activity: [POST] Создание группового события
          - get_activity: [GET] Чтение группового события
          - update_activity: [PUT] Обновление группового события
          - delete_activity: [DELETE] Удаление группового события
          - get_activity_filters: [GET] Фильтры групповых событий
          - get_activity_search_dates_range: [GET] Поиск диапазона дат групповых событий
          - get_activity_search_dates: [GET] Поиск дат групповых событий
          - get_activity_search: [GET] Поиск групповых событий
          - get_activity_services_staff_id_1_term_test: [GET] Поиск групповых услуг
          - get_activity_duplication_strategy: [GET] Получение стратегий дублирования групповых событий
          - create_activity_duplication_strategy: [POST] Создание шаблона дублирования группового события
          - create_activity_duplication_strategy_2: [POST] Обновление шаблона дублирования группового события
          - create_activity_duplicate: [POST] Запрос дублирования группового события
          - create_companies_activities: [POST] Создание события
          - get_companies_activities: [GET] Чтение события
          - update_companies_activities: [PUT] Обновление события
          - delete_companies_activities: [DELETE] Удаление события
          - create_activities_records: [POST] Создание записи в событии
          - create_activities_records_2: [POST] Создание записи в событии

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
