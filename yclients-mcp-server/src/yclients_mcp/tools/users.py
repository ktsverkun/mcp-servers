"""YCLIENTS MCP tools: Users — manage users, roles, and permissions"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "get_users_roles": ("GET", "/api/v1/company/{company_id}/users/roles", True),
    "get_users_roles_2": ("GET", "/api/v1/company/{company_id}/users/{user_id}/roles", True),
    "get_users_permissions": (
        "GET",
        "/api/v1/company/{company_id}/users/{user_id}/permissions",
        True,
    ),
    "update_users_permissions": (
        "PUT",
        "/api/v1/company/{company_id}/users/{user_id}/permissions",
        True,
    ),
    "create_users_copy_to_companies": (
        "POST",
        "/api/v1/company/{company_id}/users/{user_id}/copy_to_companies",
        True,
    ),
    "create_users_remove_from_companies": (
        "POST",
        "/api/v1/company/{company_id}/users/{user_id}/remove_from_companies",
        True,
    ),
    "list_user_permissions": ("GET", "/api/v1/user/permissions/{company_id}", True),
    "create_user_invite": ("POST", "/api/v1/user/invite/{salon_id}", True),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_users(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Users — manage users, roles, and permissions

        Available operations:
          - get_users_roles: [GET] Получение списка ролей пользователей
          - get_users_roles_2: [GET] Получение списка ролей в контексте существующего пользователя
          - get_users_permissions: [GET] Получение значений прав и роли пользователя
          - update_users_permissions: [PUT] Обновление прав и роли пользователя
          - create_users_copy_to_companies: [POST] Копирование пользователя в филиалы
          - create_users_remove_from_companies: [POST] Удаление пользователя из филиалов
          - list_user_permissions: [GET] Получить список прав
          - create_user_invite: [POST] Создание и отправка приглашения

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
