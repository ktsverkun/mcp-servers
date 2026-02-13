"""YCLIENTS MCP tools: Notifications — notification settings"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "get_notification_settings_notification_types": (
        "GET",
        "/api/v1/notification_settings/{company_id}/notification_types",
        True,
    ),
    "get_notification_settings_users": (
        "GET",
        "/api/v1/notification_settings/{company_id}/users/{user_id}",
        True,
    ),
    "create_notification_settings_users": (
        "POST",
        "/api/v1/notification_settings/{company_id}/users/{user_id}",
        True,
    ),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_notifications(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Notifications — notification settings

        Available operations:
          - get_notification_settings_notification_types: [GET] Получить настройки уведомлений в филиале
          - get_notification_settings_users: [GET] Получить настройки уведомлений пользователя
          - create_notification_settings_users: [POST] Изменить настройки PUSH-уведомлений пользователя

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
