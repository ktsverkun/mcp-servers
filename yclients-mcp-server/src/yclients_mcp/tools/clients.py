"""YCLIENTS MCP tools: Clients — manage, search, import clients and network clients"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "create_clients_search": ("POST", "/api/v1/company/{company_id}/clients/search", True),
    "list_clients": ("GET", "/api/v1/clients/{company_id}", True),
    "create_clients": ("POST", "/api/v1/clients/{company_id}", True),
    "create_clients_bulk": ("POST", "/api/v1/clients/{company_id}/bulk", True),
    "get_clients_files": ("GET", "/api/v1/company/{company_id}/clients/files/{client_id}", True),
    "delete_clients_files": (
        "DELETE",
        "/api/v1/company/{company_id}/clients/files/{client_id}/{file_id}",
        False,
    ),
    "search_visits_search": ("POST", "/api/v1/company/{company_id}/clients/visits/search", True),
    "get_client": ("GET", "/api/v1/client/{company_id}/{id}", True),
    "update_client": ("PUT", "/api/v1/client/{company_id}/{id}", True),
    "delete_client": ("DELETE", "/api/v1/client/{company_id}/{id}", True),
    "get_clients_comments": (
        "GET",
        "/api/v1/company/{company_id}/clients/{client_id}/comments",
        True,
    ),
    "create_clients_comments": (
        "POST",
        "/api/v1/company/{company_id}/clients/{client_id}/comments",
        True,
    ),
    "delete_clients_comments": (
        "DELETE",
        "/api/v1/company/{company_id}/clients/{client_id}/comments/{comment_id}",
        True,
    ),
    "get_group_clients": ("GET", "/api/v1/group/{group_id}/clients/", True),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_clients(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Clients — manage, search, import clients and network clients

        Available operations:
          - create_clients_search: [POST] Получить список клиентов
          - list_clients: [GET] Устаревшее. Получить список клиентов
          - create_clients: [POST] Добавить клиента
          - create_clients_bulk: [POST] Массовое добавление клиентов
          - get_clients_files: [GET] Пример запроса на получение списка файлов клиента
          - delete_clients_files: [DELETE] Пример запроса на удаление
          - search_visits_search: [POST] Поиск по истории посещений клиента
          - get_client: [GET] Получить клиента
          - update_client: [PUT] Редактировать клиента
          - delete_client: [DELETE] Удалить клиента
          - get_clients_comments: [GET] Получение списка комментариев к клиенту
          - create_clients_comments: [POST] Добавление комментария к клиенту
          - delete_clients_comments: [DELETE] Удаление комментария к клиенту
          - get_group_clients: [GET] Получить сетевого клиента по номеру телефона.

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
