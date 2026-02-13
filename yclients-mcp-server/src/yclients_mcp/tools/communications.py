"""YCLIENTS MCP tools: Communications — SMS campaigns, email campaigns, SMS providers"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "send_clients_by_id": ("POST", "/api/v1/sms/clients/by_id/{company_id}", True),
    "send_clients_by_filter": ("POST", "/api/v1/sms/clients/by_filter/{company_id}", True),
    "send_clients_by_id_2": ("POST", "/api/v1/email/clients/by_id/{company_id}", True),
    "send_clients_by_filter_2": ("POST", "/api/v1/email/clients/by_filter/{company_id}", True),
    "create_call": ("POST", "/api/v1/", False),
    "create_delivery_status": ("POST", "/api/v1/delivery/status", False),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_communications(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Communications — SMS campaigns, email campaigns, SMS providers

        Available operations:
          - send_clients_by_id: [POST] Отправить SMS рассылку по списку клиентов
          - send_clients_by_filter: [POST] Отправить SMS рассылку по клиентам, подходящим под фильтры
          - send_clients_by_id_2: [POST] Отправить Email рассылку по списку клиентов
          - send_clients_by_filter_2: [POST] Отправить Email рассылку по клиентам, подходящим под фильтры
          - create_call: [POST] Отправка СМС
          - create_delivery_status: [POST] Получение статусов сообщений

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
