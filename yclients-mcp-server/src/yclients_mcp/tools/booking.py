"""YCLIENTS MCP tools: Online booking — forms, dates, staff, services, sessions, user records"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "get_bookform": ("GET", "/api/v1/bookform/{id}", False),
    "get_i18n": ("GET", "/api/v1/i18n/{langCode}", False),
    "send_book_code": ("POST", "/api/v1/book_code/{company_id}", False),
    "create_book_check": ("POST", "/api/v1/book_check/{company_id}", False),
    "create_book_record": ("POST", "/api/v1/book_record/{company_id}", False),
    "update_book_record": ("PUT", "/api/v1/book_record/{company_id}/{record_id}", False),
    "get_book_record": ("GET", "/api/v1/book_record/{company_id}/{record_id}/{record_hash}", True),
    "create_activity_book": ("POST", "/api/v1/activity/{company_id}/{activity_id}/book", False),
    "list_book_dates": ("GET", "/api/v1/book_dates/{company_id}", False),
    "list_book_services": ("GET", "/api/v1/book_services/{company_id}", False),
    "list_book_staff_seances": (
        "GET",
        "/api/v1/book_staff_seances/{company_id}/{staff_id}/",
        False,
    ),
    "list_book_staff": ("GET", "/api/v1/book_staff/{company_id}", False),
    "list_book_times": ("GET", "/api/v1/book_times/{company_id}/{staff_id}/{date}", False),
    "get_settings_timeslots": ("GET", "/api/v1/company/{company_id}/settings/timeslots", True),
    "send_book_code_2": ("POST", "/api/v1/book_code/{company_id}", False),
    "auth_user_auth": ("POST", "/api/v1/user/auth", False),
    "auth_booking_auth": ("POST", "/api/v1/booking/auth", False),
    "get_user_phone_confirmation": ("GET", "/api/v1/booking/user/phone_confirmation", True),
    "update_user_password": ("PUT", "/api/v1/booking/user/password", True),
    "update_booking_user": ("PUT", "/api/v1/booking/user", True),
    "get_user_data": ("GET", "/api/v1/booking/user/data", True),
    "get_user_records": ("GET", "/api/v1/user/records/{record_id}/{record_hash}", True),
    "delete_user_records": ("DELETE", "/api/v1/user/records/{record_id}/{record_hash}", True),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_booking(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Online booking — forms, dates, staff, services, sessions, user records

        Available operations:
          - get_bookform: [GET] Получить настройки формы бронирования
          - get_i18n: [GET] Получить параметры интернационализации
          - send_book_code: [POST] Отправить СМС код подтверждения номера телефона
          - create_book_check: [POST] Проверить параметры записи
          - create_book_record: [POST] Создать запись на сеанс
          - update_book_record: [PUT] Перенести запись на сеанс
          - get_book_record: [GET] Получить запись на сеанс
          - create_activity_book: [POST] Создать запись в групповом событии
          - list_book_dates: [GET] Получить список дат доступных для бронирования
          - list_book_services: [GET] Получить список услуг доступных для бронирования
          - list_book_staff_seances: [GET] Получить список ближайших доступных сеансов
          - list_book_staff: [GET] Получить список сотрудников доступных для бронирования
          - list_book_times: [GET] Получить список сеансов доступных для бронирования
          - get_settings_timeslots: [GET] Получить настройки таймслотов филиала
          - send_book_code_2: [POST] Отправить СМС код подтверждения номера телефона
          - auth_user_auth: [POST] Авторизоваться по номеру телефона и коду
          - auth_booking_auth: [POST] Авторизовать пользователя онлайн-записи
          - get_user_phone_confirmation: [GET] Отправить СМС код подтверждения номера телефона для изменения данных
          - update_user_password: [PUT] Обновление пароля пользователя онлайн-записи
          - update_booking_user: [PUT] Обновление данных пользователя онлайн-записи
          - get_user_data: [GET] Получение данных пользователя онлайн-записи
          - get_user_records: [GET] Получить записи пользователя
          - delete_user_records: [DELETE] Удалить запись пользователя

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
