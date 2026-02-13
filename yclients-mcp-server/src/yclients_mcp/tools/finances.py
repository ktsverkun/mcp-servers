"""YCLIENTS MCP tools: Finances — cash registers, transactions, KKM, sales operations"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "get_accounts": ("GET", "/api/v1/accounts/{company_id}", True),
    "get_transactions": ("GET", "/api/v1/transactions/{company_id}", True),
    "get_timetable_transactions": ("GET", "/api/v1/timetable/transactions/{company_id}", True),
    "create_finance_transactions": ("POST", "/api/v1/finance_transactions/{company_id}", True),
    "get_finance_transactions": (
        "GET",
        "/api/v1/finance_transactions/{company_id}/{transaction_id}",
        True,
    ),
    "update_finance_transactions": (
        "PUT",
        "/api/v1/finance_transactions/{company_id}/{transaction_id}",
        True,
    ),
    "delete_finance_transactions": (
        "DELETE",
        "/api/v1/finance_transactions/{company_id}/{transaction_id}",
        True,
    ),
    "get_kkm_transactions": ("GET", "/api/v1/kkm_transactions/{company_id}", True),
    "create_kkm_transactions_print_document_bill": (
        "POST",
        "/api/v1/kkm_transactions/{company_id}/print_document_bill",
        True,
    ),
    "get_company_sale": ("GET", "/api/v1/company/{company_id}/sale/{document_id}", True),
    "delete_payment_payment_transaction": (
        "DELETE",
        "/api/v1/company/{company_id}/sale/{document_id}/payment/payment_transaction/{payment_transaction_id}",
        True,
    ),
    "delete_payment_loyalty_transaction": (
        "DELETE",
        "/api/v1/company/{company_id}/sale/{document_id}/payment/loyalty_transaction/{payment_transaction_id}",
        True,
    ),
    "create_sale_payment": (
        "POST",
        "/api/v1/company/{company_id}/sale/{document_id}/payment",
        True,
    ),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_finances(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Finances — cash registers, transactions, KKM, sales operations

        Available operations:
          - get_accounts: [GET] Получить кассы компании
          - get_transactions: [GET] Получить транзакции
          - get_timetable_transactions: [GET] Получение транзакций по ID визита или записи
          - create_finance_transactions: [POST] Создание финансовой транзакции
          - get_finance_transactions: [GET] Получение финансовой транзакции
          - update_finance_transactions: [PUT] Обновление финансовой транзакции
          - delete_finance_transactions: [DELETE] Удаление транзакции
          - get_kkm_transactions: [GET] Получить транзакции
          - create_kkm_transactions_print_document_bill: [POST] Напечатать чек
          - get_company_sale: [GET] Получение Операции продажи
          - delete_payment_payment_transaction: [DELETE] Удаление транзакции оплаты в кассу
          - delete_payment_loyalty_transaction: [DELETE] Удаление транзакции оплаты лояльностью
          - create_sale_payment: [POST] Оплата в кассу и лояльностью (различными методами)

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
