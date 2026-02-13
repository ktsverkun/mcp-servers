"""YCLIENTS MCP tools: Marketplace — marketplace integrations and webhooks"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "create_callback_redirect": ("POST", "/marketplace/partner/callback/redirect", False),
    "create_partner_callback": ("POST", "/marketplace/partner/callback", False),
    "create_partner_payment": ("POST", "/marketplace/partner/payment", False),
    "create_partner_short_names": ("POST", "/marketplace/partner/short_names", False),
    "create_payment_refund": ("POST", "/marketplace/partner/payment/refund/{payment_id}", False),
    "create_marketplace_webhook": ("POST", "/marketplace_webhook", False),
    "get_salon_application": (
        "GET",
        "/marketplace/salon/{salon_id}/application/{application_id}",
        False,
    ),
    "get_application_salons": ("GET", "/marketplace/application/{application_id}/salons", False),
    "create_application_uninstall": (
        "POST",
        "/marketplace/salon/{salon_id}/application/{application_id}/uninstall",
        False,
    ),
    "get_application_payment_link": ("GET", "/marketplace/application/payment_link", False),
    "get_application_tariffs": ("GET", "/marketplace/application/{application_id}/tariffs", False),
    "create_application_add_discount": ("POST", "/marketplace/application/add_discount", False),
    "create_application_update_channel": ("POST", "/marketplace/application/update_channel", False),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_marketplace(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Marketplace — marketplace integrations and webhooks

        Available operations:
          - create_callback_redirect: [POST] Адрес для редиректа пользователя после регистрации в сервисе-партнере
          - create_partner_callback: [POST] Установка приложения для филиала
          - create_partner_payment: [POST] Уведомление YCLIENTS об успешном платеже
          - create_partner_short_names: [POST] Оповещение YCLIENTS о доступных именах отправителя SMS-сообщений
          - create_payment_refund: [POST] Уведомление о возврате платежа
          - create_marketplace_webhook: [POST] Вебхук из YCLIENTS о событиях
          - get_salon_application: [GET] Данные о подключении приложения в салоне
          - get_application_salons: [GET] Данные о салонах, подключивших приложение
          - create_application_uninstall: [POST] Отключение приложения
          - get_application_payment_link: [GET] Генерация ссылки на оплату
          - get_application_tariffs: [GET] Данные о тарифах приложения
          - create_application_add_discount: [POST] Установить скидку салонам на оплату
          - create_application_update_channel: [POST] Изменение доступности каналов отправки

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
