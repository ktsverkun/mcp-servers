"""YCLIENTS MCP tools: Services — manage service categories and individual services"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "create_service_categories": ("POST", "/api/v1/service_categories/{company_id}", True),
    "get_service_category": ("GET", "/api/v1/service_category/{company_id}/{id}", False),
    "update_service_category": ("PUT", "/api/v1/service_category/{company_id}/{id}", True),
    "delete_service_category": ("DELETE", "/api/v1/service_category/{company_id}/{id}", True),
    "list_chain_service_categories": ("GET", "/api/v1/chain/{chain_id}/service_categories", True),
    "list_company_service_categories": (
        "GET",
        "/api/v1/company/{company_id}/service_categories/{id}",
        True,
    ),
    "list_service_categories": ("GET", "/api/v1/service_categories/{company_id}/{id}", False),
    "create_services": ("POST", "/api/v1/services/{company_id}", True),
    "list_company_services": ("GET", "/api/v1/company/{company_id}/services/{service_id}", True),
    "patch_company_services": ("PATCH", "/api/v1/company/{company_id}/services/{service_id}", True),
    "list_services": ("GET", "/api/v1/services/{company_id}/{service_id}", False),
    "update_services": ("PUT", "/api/v1/services/{company_id}/{service_id}", True),
    "delete_services": ("DELETE", "/api/v1/services/{company_id}/{service_id}", True),
    "create_services_links": ("POST", "/api/v1/company/{company_id}/services/links", False),
    "create_services_staff": (
        "POST",
        "/api/v1/company/{company_id}/services/{service_id}/staff",
        True,
    ),
    "update_services_staff": (
        "PUT",
        "/api/v1/company/{company_id}/services/{service_id}/staff/{master_id}",
        True,
    ),
    "delete_services_staff": (
        "DELETE",
        "/api/v1/company/{company_id}/services/{service_id}/staff/{master_id}",
        True,
    ),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_services(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Services — manage service categories and individual services

        Available operations:
          - create_service_categories: [POST] Создать категорию услугу
          - get_service_category: [GET] Получить категорию услуг
          - update_service_category: [PUT] Изменить категорию услуг
          - delete_service_category: [DELETE] Удалить категорию услуг
          - list_chain_service_categories: [GET] Получить список категорий услуг сети
          - list_company_service_categories: [GET] Получить список категорий услуг
          - list_service_categories: [GET] Устаревшее. Получить список категорий услуг
          - create_services: [POST] Создать услугу
          - list_company_services: [GET] Получить список услуг / конкретную услугу
          - patch_company_services: [PATCH] Изменить услугу
          - list_services: [GET] Устаревшее. Получить список услуг / конкретную услугу
          - update_services: [PUT] Устаревшее. Изменить услугу
          - delete_services: [DELETE] Удалить услугу
          - create_services_links: [POST] Изменить длительность оказания услуги сотрудниками, технические карты, названия на других языках
          - create_services_staff: [POST] Привязка сотрудника, оказывающего услугу
          - update_services_staff: [PUT] Изменение настроек оказания услуги сотрудником
          - delete_services_staff: [DELETE] Отвязка сотрудника, оказывающего услугу

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
