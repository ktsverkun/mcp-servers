"""YCLIENTS MCP tools: Fiscalization — receipt fiscalization for partners"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "create_https__your_api_url": ("POST", "/api/v1/https://your-api.url", False),
    "get_references_tax_system": (
        "GET",
        "/api/v1/integration/kkm/references/tax_system/{countryId}",
        False,
    ),
    "create_kkm_callback": ("POST", "/api/v1/integration/kkm/callback/", False),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_fiscalization(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Fiscalization — receipt fiscalization for partners

        Available operations:
          - create_https__your_api_url: [POST] Пример запроса на фискализацию документа
          - get_references_tax_system: [GET] Пример запроса на получение списка
          - create_kkm_callback: [POST] Пример запроса в случае успешной фискализации или в случае ошибка

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
