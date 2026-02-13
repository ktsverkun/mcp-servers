"""YCLIENTS MCP tools: Personal Accounts — manage personal client accounts"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "create_deposits_operations": ("POST", "/api/v1/deposits_operations/{salon_id}", True),
    "get_company_client": ("GET", "/api/v1/deposits/company/{company_id}/client/{client_id}", True),
    "get_deposits_chain": ("GET", "/api/v1/deposits/chain/{chain_id}", True),
    "get_chain_phone": ("GET", "/api/v1/deposits/chain/{chain_id}/phone/{phone}", True),
    "get_chain_deposit_history": (
        "GET",
        "/api/v1/deposits/chain/{chain_id}/deposit_history/{deposit_id}",
        True,
    ),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_personal_accounts(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Personal Accounts — manage personal client accounts

        Available operations:
          - create_deposits_operations: [POST] Создание операции пополнения личного счёта
          - get_company_client: [GET] Получение списка личных счетов по филиалу и клиенту
          - get_deposits_chain: [GET] Получение списка личных счетов по сети и набору фильтров
          - get_chain_phone: [GET] Получение списка личных счетов по сети и номеру телефона клиента
          - get_chain_deposit_history: [GET] Получение истории операции личного счета

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
