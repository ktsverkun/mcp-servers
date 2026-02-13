"""YCLIENTS MCP tools: Inventory — warehouses, operations, documents, goods transactions"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "get_storages": ("GET", "/api/v1/storages/{company_id}", True),
    "get_storages_transactions": ("GET", "/api/v1/storages/transactions/{company_id}", True),
    "create_storage_operations_goods_transactions": (
        "POST",
        "/api/v1/storage_operations/goods_transactions/{company_id}",
        True,
    ),
    "get_storage_operations_goods_transactions": (
        "GET",
        "/api/v1/storage_operations/goods_transactions/{company_id}/{transaction_id}",
        True,
    ),
    "update_storage_operations_goods_transactions": (
        "PUT",
        "/api/v1/storage_operations/goods_transactions/{company_id}/{transaction_id}",
        True,
    ),
    "delete_storage_operations_goods_transactions": (
        "DELETE",
        "/api/v1/storage_operations/goods_transactions/{company_id}/{transaction_id}",
        True,
    ),
    "create_storage_operations_operation": (
        "POST",
        "/api/v1/storage_operations/operation/{company_id}",
        True,
    ),
    "create_storage_operations_documents": (
        "POST",
        "/api/v1/storage_operations/documents/{company_id}",
        True,
    ),
    "get_storage_operations_documents": (
        "GET",
        "/api/v1/storage_operations/documents/{company_id}/{document_id}",
        True,
    ),
    "update_storage_operations_documents": (
        "PUT",
        "/api/v1/storage_operations/documents/{company_id}/{document_id}",
        True,
    ),
    "delete_storage_operations_documents": (
        "DELETE",
        "/api/v1/storage_operations/documents/{company_id}/{document_id}",
        True,
    ),
    "get_documents_finance_transactions": (
        "GET",
        "/api/v1/storage_operations/documents/finance_transactions/{document_id}",
        True,
    ),
    "get_documents_goods_transactions": (
        "GET",
        "/api/v1/storage_operations/documents/goods_transactions/{document_id}",
        True,
    ),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_inventory(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Inventory — warehouses, operations, documents, goods transactions

        Available operations:
          - get_storages: [GET] Получить склады компании
          - get_storages_transactions: [GET] Поиск товарных транзакций
          - create_storage_operations_goods_transactions: [POST] Создать транзакцию
          - get_storage_operations_goods_transactions: [GET] Получение транзакции
          - update_storage_operations_goods_transactions: [PUT] Обновление транзакции
          - delete_storage_operations_goods_transactions: [DELETE] Удаление транзакции
          - create_storage_operations_operation: [POST] Создание складской операции
          - create_storage_operations_documents: [POST] Создать документ
          - get_storage_operations_documents: [GET] Получить документ
          - update_storage_operations_documents: [PUT] Обновить документ
          - delete_storage_operations_documents: [DELETE] Удалить документ
          - get_documents_finance_transactions: [GET] Получить финансовые транзакции документа
          - get_documents_goods_transactions: [GET] Получить товарные транзакции документа

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
