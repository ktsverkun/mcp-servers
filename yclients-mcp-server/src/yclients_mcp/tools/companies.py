"""YCLIENTS MCP tools: Companies — list, get, create, update companies and company users"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "list_companies": ("GET", "/api/v1/companies", False),
    "create_companies": ("POST", "/api/v1/companies", True),
    "get_company": ("GET", "/api/v1/company/{id}/", True),
    "update_company": ("PUT", "/api/v1/company/{id}/", True),
    "delete_company": ("DELETE", "/api/v1/company/{id}/", True),
    "get_company_users": ("GET", "/api/v1/company_users/{company_id}", True),
    "get_company_users_2": ("GET", "/api/v1/company/{company_id}/users", True),
    "delete_company_users": ("DELETE", "/api/v1/company/{company_id}/users/{user_id}", True),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_companies(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Companies — list, get, create, update companies and company users

        Available operations:
          - list_companies: [GET] Получить список компаний
          - create_companies: [POST] Создать компанию
          - get_company: [GET] Получить компанию
          - update_company: [PUT] Изменить компанию
          - delete_company: [DELETE] Удалить компанию
          - get_company_users: [GET] Устаревшее. Получить пользователей компании
          - get_company_users_2: [GET] Получить пользователей компании
          - delete_company_users: [DELETE] Удалить пользователя в компании

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
