"""YCLIENTS MCP tools: Schedule — staff schedules, journal dates/sessions, waiting list"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "list_timetable_dates": ("GET", "/api/v1/timetable/dates/{company_id}/{date}", True),
    "get_staff_schedule": ("GET", "/api/v1/company/{company_id}/staff/schedule", True),
    "update_staff_schedule": ("PUT", "/api/v1/company/{company_id}/staff/schedule", True),
    "get_schedule": (
        "GET",
        "/api/v1/schedule/{company_id}/{staff_id}/{start_date}/{end_date}",
        True,
    ),
    "update_schedule": ("PUT", "/api/v1/schedule/{company_id}/{staff_id}", True),
    "list_timetable_seances": (
        "GET",
        "/api/v1/timetable/seances/{company_id}/{staff_id}/{date}",
        True,
    ),
    "get_schedules_search": (
        "GET",
        "/api/v1/company/{company_id}/schedules/search/{entity_type}/{entity_id}",
        True,
    ),
    "create_company_schedules": ("POST", "/api/v1/company/{company_id}/schedules", True),
    "patch_company_schedules": (
        "PATCH",
        "/api/v1/company/{company_id}/schedules/{schedule_id}",
        True,
    ),
    "delete_company_schedules": (
        "DELETE",
        "/api/v1/company/{company_id}/schedules/{schedule_id}",
        False,
    ),
    "create_schedules_days": (
        "POST",
        "/api/v1/company/{company_id}/schedules/{schedule_id}/days",
        True,
    ),
    "patch_schedules_days": (
        "PATCH",
        "/api/v1/company/{company_id}/schedules/{schedule_id}/days/{day_id}",
        True,
    ),
    "delete_schedules_days": (
        "DELETE",
        "/api/v1/company/{company_id}/schedules/{schedule_id}/days/{day_id}",
        False,
    ),
    "get_days_events": (
        "GET",
        "/api/v1/company/{company_id}/schedules/{schedule_id}/days/{day_id}/events",
        True,
    ),
    "create_schedules_client_schedules": (
        "POST",
        "/api/v1/company/{company_id}/schedules/{schedule_id}/client_schedules",
        True,
    ),
    "patch_schedules_client_schedules": (
        "PATCH",
        "/api/v1/company/{company_id}/schedules/{schedule_id}/client_schedules/{client_schedule_id}",
        True,
    ),
    "delete_schedules_client_schedules": (
        "DELETE",
        "/api/v1/company/{company_id}/schedules/{schedule_id}/client_schedules/{client_schedule_id}",
        False,
    ),
    "get_abonements_search_for_activity": (
        "GET",
        "/api/v1/company/{company_id}/client/{client_id}/loyalty/abonements/search_for_activity/",
        True,
    ),
    "get_abonements_check_for_activity": (
        "GET",
        "/api/v1/company/{company_id}/client/{client_id}/loyalty/abonements/{abonement_id}/check_for_activity/",
        True,
    ),
    "get_companies_waiting_list": ("GET", "/api/v2/companies/{company_id}/waiting_list", False),
    "create_companies_waiting_list": ("POST", "/api/v2/companies/{company_id}/waiting_list", False),
    "update_companies_waiting_list": (
        "PUT",
        "/api/v2/companies/{company_id}/waiting_list/{waiting_list_entry_id}",
        False,
    ),
    "delete_companies_waiting_list": (
        "DELETE",
        "/api/v2/companies/{company_id}/waiting_list/{waiting_list_entry_id}",
        False,
    ),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_schedule(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Schedule — staff schedules, journal dates/sessions, waiting list

        Available operations:
          - list_timetable_dates: [GET] Получить список дат для журнала
          - get_staff_schedule: [GET] Получение графиков работы сотрудников
          - update_staff_schedule: [PUT] Установка графиков работы сотрудников
          - get_schedule: [GET] Устаревшее. Получить расписание сотрудника
          - update_schedule: [PUT] Устаревшее. Изменить расписание работы сотрудника
          - list_timetable_seances: [GET] Получить список сеансов для журнала
          - get_schedules_search: [GET] Поиск расписания по сущности
          - create_company_schedules: [POST] Создание расписания
          - patch_company_schedules: [PATCH] Обновление расписания
          - delete_company_schedules: [DELETE] Удаление расписания
          - create_schedules_days: [POST] Создание серии расписания
          - patch_schedules_days: [PATCH] Обновление серии расписания
          - delete_schedules_days: [DELETE] Удаление серии расписания
          - get_days_events: [GET] Получение списка сущностей записей/событий в рамках серии расписания
          - create_schedules_client_schedules: [POST] Создание графика посещений клиента
          - patch_schedules_client_schedules: [PATCH] Обновление графика посещений клиента
          - delete_schedules_client_schedules: [DELETE] Удаление графика посещений клиента
          - get_abonements_search_for_activity: [GET] Чтение доступных абонементов
          - get_abonements_check_for_activity: [GET] Проверка абонемента на количество доступных записей и последнюю дату записи
          - get_companies_waiting_list: [GET] Получить заявки в листе ожидания

          - create_companies_waiting_list: [POST] Создание заявки в листе ожидания

          - update_companies_waiting_list: [PUT] Обновление заявки в листе ожидания

          - delete_companies_waiting_list: [DELETE] Удаление заявки в листе ожидания


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
