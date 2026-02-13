"""YCLIENTS MCP tools: Loyalty — programs, cards, certificates, subscriptions, visit loyalty"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "list_card_types_salon": ("GET", "/api/v1/loyalty/card_types/salon/{company_id}", True),
    "list_loyalty_cards": ("GET", "/api/v1/loyalty/cards/{phone}/{group_id}/{company_id}", True),
    "list_loyalty_client_cards": ("GET", "/api/v1/loyalty/client_cards/{client_id}", True),
    "get_user_loyalty_cards": ("GET", "/api/v1/user/loyalty_cards/{group_id}", True),
    "create_loyalty_cards": ("POST", "/api/v1/loyalty/cards/{company_id}", True),
    "delete_loyalty_cards": ("DELETE", "/api/v1/loyalty/cards/{company_id}/{card_id}", True),
    "create_cards_manual_transaction": (
        "POST",
        "/api/v1/chain/{chain_id}/loyalty/cards/{card_id}/manual_transaction",
        True,
    ),
    "list_loyalty_card_types": ("GET", "/api/v1/chain/{chain_id}/loyalty/card_types", True),
    "create_cards_manual_transaction_2": (
        "POST",
        "/api/v1/company/{company_id}/loyalty/cards/{card_id}/manual_transaction",
        True,
    ),
    "list_card_types_client": (
        "GET",
        "/api/v1/loyalty/card_types/client/{company_id}/{phone}",
        True,
    ),
    "create_loyalty_apply_discount_program": (
        "POST",
        "/api/v1/visit/loyalty/apply_discount_program/{company_id}/{card_id}/{program_id}",
        True,
    ),
    "create_loyalty_cancel_discount_program": (
        "POST",
        "/api/v1/visit/loyalty/cancel_discount_program/{company_id}/{card_id}/{program_id}",
        True,
    ),
    "create_loyalty_apply_card_withdrawal": (
        "POST",
        "/api/v1/visit/loyalty/apply_card_withdrawal/{company_id}/{card_id}",
        True,
    ),
    "create_loyalty_cancel_card_withdrawal": (
        "POST",
        "/api/v1/visit/loyalty/cancel_card_withdrawal/{company_id}/{card_id}",
        True,
    ),
    "create_loyalty_apply_referral_program": (
        "POST",
        "/api/v1/visit/loyalty/apply_referral_program/{company_id}/{group_id}",
        True,
    ),
    "get_loyalty_transactions": ("GET", "/api/v1/visit/loyalty/transactions/{visit_id}", True),
    "list_notification_message_templates_programs": (
        "GET",
        "/api/v1/chain/{chain_id}/loyalty/notification_message_templates/programs",
        True,
    ),
    "create_loyalty_programs": ("POST", "/api/v1/chain/{chain_id}/loyalty/programs/", True),
    "get_loyalty_programs": (
        "GET",
        "/api/v1/chain/{chain_id}/loyalty/programs/{loyalty_program_id}",
        True,
    ),
    "update_loyalty_programs": (
        "PUT",
        "/api/v1/chain/{chain_id}/loyalty/programs/{loyalty_program_id}",
        False,
    ),
    "delete_loyalty_programs": (
        "DELETE",
        "/api/v1/chain/{chain_id}/loyalty/programs/{loyalty_program_id}",
        False,
    ),
    "list_loyalty_transactions": ("GET", "/api/v1/chain/{chain_id}/loyalty/transactions", True),
    "get_loyalty_generate_code": (
        "GET",
        "/api/v1/loyalty/generate_code/{company_id}/{good_Id}",
        True,
    ),
    "list_abonement_types_search": (
        "GET",
        "/api/v1/company/{company_id}/loyalty/abonement_types/search",
        True,
    ),
    "list_abonement_types_fetch": (
        "GET",
        "/api/v1/company/{company_id}/loyalty/abonement_types/fetch",
        True,
    ),
    "list_certificate_types_search": (
        "GET",
        "/api/v1/company/{company_id}/loyalty/certificate_types/search",
        True,
    ),
    "list_certificate_types_fetch": (
        "GET",
        "/api/v1/company/{company_id}/loyalty/certificate_types/fetch",
        True,
    ),
    "list_programs_search": ("GET", "/api/v1/company/{company_id}/loyalty/programs/search", True),
    "get_loyalty_programs_visits": (
        "GET",
        "/api/v1/company/{company_id}/analytics/loyalty_programs/visits",
        True,
    ),
    "get_loyalty_programs_income": (
        "GET",
        "/api/v1/company/{company_id}/analytics/loyalty_programs/income/",
        True,
    ),
    "get_loyalty_programs_staff": (
        "GET",
        "/api/v1/company/{company_id}/analytics/loyalty_programs/staff/",
        True,
    ),
    "create_abonements_freeze": (
        "POST",
        "/api/v1/chain/{chain_id}/loyalty/abonements/{abonementId}/freeze",
        True,
    ),
    "create_abonements_unfreeze": (
        "POST",
        "/api/v1/chain/{chain_id}/loyalty/abonements/{abonementId}/unfreeze",
        True,
    ),
    "create_abonements_set_period": (
        "POST",
        "/api/v1/chain/{chain_id}/loyalty/abonements/{abonementId}/set_period",
        True,
    ),
    "create_abonements_set_balance": (
        "POST",
        "/api/v1/chain/{chain_id}/loyalty/abonements/{abonementId}/set_balance",
        True,
    ),
    "list_loyalty_abonements": ("GET", "/api/v1/chain/{chain_id}/loyalty/abonements", True),
    "get_loyalty_abonements": ("GET", "/api/v1/loyalty/abonements/", True),
    "get_loyalty_abonements_2": ("GET", "/api/v1/user/loyalty/abonements/", True),
    "get_loyalty_certificates": ("GET", "/api/v1/loyalty/certificates/", True),
    "get_loyalty_certificates_2": ("GET", "/api/v1/user/loyalty/certificates/", True),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_loyalty(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Loyalty — programs, cards, certificates, subscriptions, visit loyalty

        Available operations:
          - list_card_types_salon: [GET] Получить список типов карт доступных в филиале
          - list_loyalty_cards: [GET] Получить список карт клиента по номеру телефона
          - list_loyalty_client_cards: [GET] Получить список карт клиента по ID
          - get_user_loyalty_cards: [GET] Получить карты лояльности пользователя
          - create_loyalty_cards: [POST] Выдать карту лояльности
          - delete_loyalty_cards: [DELETE] Удалить карту  лояльности
          - create_cards_manual_transaction: [POST] Ручное списание/пополнение карты лояльности в сети
          - list_loyalty_card_types: [GET] Получить список типов карт, доступных в сети
          - create_cards_manual_transaction_2: [POST] Ручное списание/пополнение карты лояльности в компании
          - list_card_types_client: [GET] Получить список типов карт доступных для выдачи клиенту
          - create_loyalty_apply_discount_program: [POST] Применить акцию скидки в визите
          - create_loyalty_cancel_discount_program: [POST] Отменить применение акции скидки в визите
          - create_loyalty_apply_card_withdrawal: [POST] Применить списание с карты лояльности в визите
          - create_loyalty_cancel_card_withdrawal: [POST] Отменить списание с карты лояльности в визите
          - create_loyalty_apply_referral_program: [POST] Применить реферальную программу в записи
          - get_loyalty_transactions: [GET] Получить транзакции лояльности по визиту
          - list_notification_message_templates_programs: [GET] Получить список шаблонов уведомлений лояльности
          - create_loyalty_programs: [POST] Создать акцию в сети
          - get_loyalty_programs: [GET] Получить акцию в сети
          - update_loyalty_programs: [PUT] Изменить акцию в сети
          - delete_loyalty_programs: [DELETE] Удалить акцию в сети
          - list_loyalty_transactions: [GET] Получить список транзакций лояльности в сети
          - get_loyalty_generate_code: [GET] Генерация кода сертификата/абонемента
          - list_abonement_types_search: [GET] Получить список доступных типов абонементов
          - list_abonement_types_fetch: [GET] Получить список типов абонементов по идентификатору
          - list_certificate_types_search: [GET] Получить список доступных типов сертификатов
          - list_certificate_types_fetch: [GET] Получить список типов сертификатов по идентификатору
          - list_programs_search: [GET] Получить список акций, действующих в филиале
          - get_loyalty_programs_visits: [GET] Получить статистику по клиентам
          - get_loyalty_programs_income: [GET] Получить статистику по выручке
          - get_loyalty_programs_staff: [GET] Получить возвращаемость по сотруднику
          - create_abonements_freeze: [POST] Заморозить абонемент
          - create_abonements_unfreeze: [POST] Разморозить абонемент
          - create_abonements_set_period: [POST] Изменить длительность абонемента
          - create_abonements_set_balance: [POST] Изменить количество использований абонемента
          - list_loyalty_abonements: [GET] Получить список абонементов по фильтру
          - get_loyalty_abonements: [GET] Получить абонементы клиента
          - get_loyalty_abonements_2: [GET] Получить абонементы пользователя
          - get_loyalty_certificates: [GET] Получить сертификаты клиента
          - get_loyalty_certificates_2: [GET] Получить сертификаты пользователя

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
