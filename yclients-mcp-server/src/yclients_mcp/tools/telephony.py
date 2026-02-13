"""YCLIENTS MCP tools: Telephony — network telephony integration"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "create_voip_integration": ("POST", "/api/v1/voip/integration", False),
    "list_integration_calls": ("GET", "/api/v1/voip/integration/calls", True),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_telephony(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Telephony — network telephony integration

        Available operations:
          - create_voip_integration: [POST] События телефонии
          - list_integration_calls: [GET] Получить список звонков филиала

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
