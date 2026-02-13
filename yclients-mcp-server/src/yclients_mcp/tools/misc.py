"""YCLIENTS MCP tools: Miscellaneous — other API operations"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "create_loyalty_abonement_types": (
        "POST",
        "/api/v1/chain/{chain_id}/loyalty/abonement_types",
        True,
    ),
    "update_loyalty_abonement_types": (
        "PUT",
        "/api/v1/chain/{chain_id}/loyalty/abonement_types/{loyalty_abonement_type_id}",
        True,
    ),
    "delete_loyalty_abonement_types": (
        "DELETE",
        "/api/v1/chain/{chain_id}/loyalty/abonement_types/{loyalty_abonement_type_id}",
        True,
    ),
    "create_loyalty_abonement_types_2": (
        "POST",
        "/api/v1/chain/{chain_id}/loyalty/abonement_types/{loyalty_abonement_type_id}",
        True,
    ),
    "patch_loyalty_abonement_types": (
        "PATCH",
        "/api/v1/chain/{chain_id}/loyalty/abonement_types/{loyalty_abonement_type_id}",
        True,
    ),
    "create_abonement_types_clone": (
        "POST",
        "/api/v1/chain/{chain_id}/loyalty/abonement_types/{loyalty_abonement_type_id}/clone",
        True,
    ),
    "list_tips_settings": ("GET", "/api/v1/tips/{company_id}/settings", True),
    "get_settings_enable": (
        "GET",
        "/api/v1/tips/{company_id}/settings/{master_tips_settings_id}/enable",
        True,
    ),
    "create_settings_disable": (
        "POST",
        "/api/v1/tips/{company_id}/settings/{master_tips_settings_id}/disable",
        True,
    ),
    "get_settings_online": ("GET", "/api/v1/company/{company_id}/settings/online", True),
    "patch_settings_online": ("PATCH", "/api/v1/company/{company_id}/settings/online", True),
    "get_settings_timetable": ("GET", "/api/v1/company/{company_id}/settings/timetable", True),
    "patch_settings_timetable": ("PATCH", "/api/v1/company/{company_id}/settings/timetable", True),
    "list_company_booking_forms": ("GET", "/api/v1/company/{company_id}/booking_forms/", True),
    "create_company_booking_forms": ("POST", "/api/v1/company/{company_id}/booking_forms/", True),
    "get_company_booking_forms": (
        "GET",
        "/api/v1/company/{company_id}/booking_forms/{form_id}/",
        True,
    ),
    "delete_company_booking_forms": (
        "DELETE",
        "/api/v1/company/{company_id}/booking_forms/{form_id}/",
        False,
    ),
    "patch_company_booking_forms": (
        "PATCH",
        "/api/v1/company/{company_id}/booking_forms/{form_id}/",
        True,
    ),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_misc(operation: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Miscellaneous — other API operations

        Available operations:
          - create_loyalty_abonement_types: [POST] Создание типа абонемента
          - update_loyalty_abonement_types: [PUT] Обновление типа абонемента
          - delete_loyalty_abonement_types: [DELETE] Удаление типа абонемента
          - create_loyalty_abonement_types_2: [POST] Восстановление удалённого типа абонемента
          - patch_loyalty_abonement_types: [PATCH] Архивация/восстановление типа абонемента
          - create_abonement_types_clone: [POST] Клонирование типа абонемента по идентификатору
          - list_tips_settings: [GET] Получить список мастеров салона с их настройками чаевых
          - get_settings_enable: [GET] Включить чаевые у мастера
          - create_settings_disable: [POST] Отключить чаевые у мастера
          - get_settings_online: [GET] Получение настроек онлайн-записи
          - patch_settings_online: [PATCH] Обновление настроек онлайн-записи
          - get_settings_timetable: [GET] Получение настроек журнала записи
          - patch_settings_timetable: [PATCH] Обновление настроек журнала записи
          - list_company_booking_forms: [GET] Получить список букформ
          - create_company_booking_forms: [POST] Создать букформу
          - get_company_booking_forms: [GET] Получить букформу
          - delete_company_booking_forms: [DELETE] Удалить букформу
          - patch_company_booking_forms: [PATCH] Изменить букформу

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
