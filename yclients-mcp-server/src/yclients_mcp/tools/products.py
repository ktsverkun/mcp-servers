"""YCLIENTS MCP tools: Products — goods, product categories, tech cards and consumables"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "get_labels": ("GET", "/api/v1/labels/{company_id}/{entity}", True),
    "create_clients_create": ("POST", "/api/v1/labels/{company_id}/clients/create", True),
    "create_labels": ("POST", "/api/v1/labels/{company_id}", True),
    "update_labels": ("PUT", "/api/v1/labels/{company_id}/{label_id}", True),
    "delete_labels": ("DELETE", "/api/v1/labels/{company_id}/{label_id}", True),
    "get_labels_clients": ("GET", "/api/v1/labels/{company_id}/clients", True),
    "get_search__term__count": (
        "GET",
        "/api/v1/goods/search/{company_id}?term={search_term}&count={max_count}",
        True,
    ),
    "get_category_node__page__count": (
        "GET",
        "/api/v1/goods/category_node/{company_id}/{category_id}?page={page}&count={count}",
        True,
    ),
    "list_goods_categories": (
        "GET",
        "/api/v1/goods_categories/{company_id}/{parent_category_id}",
        True,
    ),
    "list_goods_categories_multiple": (
        "GET",
        "/api/v1/goods_categories/multiple/{company_id}",
        True,
    ),
    "get_company_goods_categories": (
        "GET",
        "/api/v1/company/{company_id}/goods_categories/{parent_category_id}",
        True,
    ),
    "create_goods_categories": ("POST", "/api/v1/goods_categories/{company_id}", True),
    "update_goods_categories": ("PUT", "/api/v1/goods_categories/{company_id}/{category_id}", True),
    "delete_goods_categories": (
        "DELETE",
        "/api/v1/goods_categories/{company_id}/{category_id}",
        True,
    ),
    "list_technological_cards": ("GET", "/api/v1/technological_cards/{company_id}/", True),
    "get_technological_cards_default_for_staff_and_serv": (
        "GET",
        "/api/v1/technological_cards/default_for_staff_and_service/{company_id}/{staffId}/{serviceId}/",
        True,
    ),
    "list_technological_cards_record_consumables": (
        "GET",
        "/api/v1/technological_cards/record_consumables/{company_id}/{record_id}/",
        True,
    ),
    "delete_record_consumables_technological_cards": (
        "DELETE",
        "/api/v1/technological_cards/record_consumables/technological_cards/{company_id}/{record_id}/{service_id}",
        True,
    ),
    "update_record_consumables_consumables": (
        "PUT",
        "/api/v1/technological_cards/record_consumables/consumables/{company_id}/{record_id}/{service_id}/",
        True,
    ),
    "create_goods": ("POST", "/api/v1/goods/{company_id}", True),
    "get_goods": ("GET", "/api/v1/goods/{company_id}/{good_id}", True),
    "update_goods": ("PUT", "/api/v1/goods/{company_id}/{good_id}", True),
    "delete_goods": ("DELETE", "/api/v1/goods/{company_id}/{good_id}", True),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_products(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Products — goods, product categories, tech cards and consumables

        Available operations:
          - get_labels: [GET] Получить категории компании
          - create_clients_create: [POST] Создать клиентскую категорию компании
          - create_labels: [POST] Создать категорию
          - update_labels: [PUT] Обновить категорию
          - delete_labels: [DELETE] Удалить категорию компании
          - get_labels_clients: [GET] Получить клиентские категории с поиском по названию
          - get_search__term__count: [GET] Пример запроса на получение списка
          - get_category_node__page__count: [GET] Пример запроса на получение состава категории
          - list_goods_categories: [GET] Получить список категорий товаров
          - list_goods_categories_multiple: [GET] Получить список категорий товаров по идентификатору
          - get_company_goods_categories: [GET] Пример запроса на получение категорий
          - create_goods_categories: [POST] Создать категорию товаров
          - update_goods_categories: [PUT] Редактировать категорию товаров
          - delete_goods_categories: [DELETE] Удалить категорию товаров
          - list_technological_cards: [GET] Получить список тех карт
          - get_technological_cards_default_for_staff_and_serv: [GET] Получить тех карту для связи сотрудник услуга
          - list_technological_cards_record_consumables: [GET] Получить список тех карт и расходников записи
          - delete_record_consumables_technological_cards: [DELETE] Удалить технологическую из связи запись-услуга
          - update_record_consumables_consumables: [PUT] Изменить список расходников связи запись-услуга
          - create_goods: [POST] Создать товар
          - get_goods: [GET] Получить товары
          - update_goods: [PUT] Редактировать товар
          - delete_goods: [DELETE] Удалить товар

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
