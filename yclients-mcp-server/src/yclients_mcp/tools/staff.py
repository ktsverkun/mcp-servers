"""YCLIENTS MCP tools: Staff — employees, positions, schedules, salary calculations"""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path

# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {
    "create_staff_quick": ("POST", "/api/v1/company/{company_id}/staff/quick", True),
    "create_staff": ("POST", "/api/v1/staff/{company_id}", True),
    "list_company_staff": ("GET", "/api/v1/company/{company_id}/staff/{staff_id}", True),
    "list_staff": ("GET", "/api/v1/staff/{company_id}/{staff_id}", False),
    "update_staff": ("PUT", "/api/v1/staff/{company_id}/{staff_id}", True),
    "delete_staff": ("DELETE", "/api/v1/staff/{company_id}/{staff_id}", True),
    "get_staff_calculation": (
        "GET",
        "/api/v1/company/{company_id}/salary/payroll/staff/{staff_id}/calculation/",
        True,
    ),
    "get_staff_calculation_2": (
        "GET",
        "/api/v1/company/{company_id}/salary/payroll/staff/{staff_id}/calculation/{calculation_id}",
        True,
    ),
    "get_staff_salary_schemes_count": (
        "GET",
        "/api/v1/company/{company_id}/salary/calculation/staff/{staff_id}/salary_schemes_count/",
        True,
    ),
    "get_calculation_staff": (
        "GET",
        "/api/v1/company/{company_id}/salary/calculation/staff/{staff_id}/",
        True,
    ),
    "get_staff_daily": (
        "GET",
        "/api/v1/company/{company_id}/salary/calculation/staff/daily/{staff_id}/",
        True,
    ),
    "get_period_staff": (
        "GET",
        "/api/v1/company/{company_id}/salary/period/staff/{staff_id}/",
        True,
    ),
    "get_staff_daily_2": (
        "GET",
        "/api/v1/company/{company_id}/salary/period/staff/daily/{staff_id}/",
        True,
    ),
    "get_staff_calculation_3": (
        "GET",
        "/api/v1/company/{company_id}/salary/staff/{staff_id}/calculation/",
        True,
    ),
    "get_staff_salary_schemes": (
        "GET",
        "/api/v1/company/{company_id}/salary/staff/{staff_id}/salary_schemes/",
        True,
    ),
    "get_staff_period": (
        "GET",
        "/api/v1/company/{company_id}/salary/staff/{staff_id}/period/",
        True,
    ),
    "list_staff_positions": ("GET", "/api/v1/company/{company_id}/staff/positions/", True),
    "create_positions_quick": ("POST", "/api/v1/company/{company_id}/positions/quick/", True),
}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def yclients_staff(
        operation: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Staff — employees, positions, schedules, salary calculations

        Available operations:
          - create_staff_quick: [POST] Быстрое создание сотрудника
          - create_staff: [POST] Устаревшее. Добавить нового сотрудника
          - list_company_staff: [GET] Получить список сотрудников / конкретного сотрудника
          - list_staff: [GET] Устаревшее. Получить список сотрудников / конкретного сотрудника
          - update_staff: [PUT] Изменить сотрудника
          - delete_staff: [DELETE] Удалить сотрудника
          - get_staff_calculation: [GET] Поиск начислений по сотруднику
          - get_staff_calculation_2: [GET] Получение данных о начислении по сотруднику
          - get_staff_salary_schemes_count: [GET] Получение количества схем расчёта зарплат у сотрудника
          - get_calculation_staff: [GET] Получение взаиморасчётов с сотрудником
          - get_staff_daily: [GET] Получение взаиморасчётов с сотрудником в разрезе по дате
          - get_period_staff: [GET] Получение расчёта зарплаты за период по сотруднику
          - get_staff_daily_2: [GET] Получение расчёта зарплаты за период по сотруднику в разрезе по дате
          - get_staff_calculation_3: [GET] Получение собственных взаиморасчётов сотрудника с филиалом
          - get_staff_salary_schemes: [GET] Получение собственных схем расчёта зарплат
          - get_staff_period: [GET] Получение расчёта собственной зарплаты за период
          - list_staff_positions: [GET] Получить список должностей компании
          - create_positions_quick: [POST] Быстрое создание должности

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
