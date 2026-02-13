#!/usr/bin/env python3
"""
YCLIENTS MCP Server — spec sync script.

Downloads the latest OpenAPI spec from developer.yclients.com,
compares it with the current one, and regenerates tool modules if changed.

Usage:
    python scripts/sync_spec.py              # check & update if changed
    python scripts/sync_spec.py --force      # force regeneration even if unchanged
    python scripts/sync_spec.py --dry-run    # check for changes without updating

Exit codes:
    0 — no changes (or updated successfully)
    1 — error
    2 — changes detected (--dry-run mode)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

# ── Paths ───────────────────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
TOOLS_DIR = os.path.join(PROJECT_ROOT, "src", "yclients_mcp", "tools")
SPEC_PATH = os.path.join(DATA_DIR, "yclients_openapi.json")
TAG_ENDPOINTS_PATH = os.path.join(DATA_DIR, "tag_endpoints.json")

YCLIENTS_DOC_URL = "https://developer.yclients.com/ru/"


# ═══════════════════════════════════════════════════════════════════════
#  STEP 1: Download HTML and extract OpenAPI spec
# ═══════════════════════════════════════════════════════════════════════

def download_html(url: str) -> str:
    """Fetch the ReDoc HTML page."""
    print(f"[1/5] Downloading {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "yclients-mcp-sync/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        html = resp.read().decode("utf-8")
    print(f"      Downloaded {len(html):,} chars")
    return html


def extract_spec_from_html(html: str) -> dict:
    """Extract OpenAPI spec from __redoc_state embedded in the HTML."""
    print("[2/5] Extracting OpenAPI spec from __redoc_state ...")
    marker = "__redoc_state ="
    start_idx = html.find(marker)
    if start_idx == -1:
        raise RuntimeError("Could not find __redoc_state in HTML")

    json_start = start_idx + len(marker)

    # Find matching closing brace with proper string tracking
    depth = 0
    in_string = False
    escape_next = False

    for i in range(json_start, len(html)):
        c = html[i]
        if escape_next:
            escape_next = False
            continue
        if c == "\\" and in_string:
            escape_next = True
            continue
        if c == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                json_end = i + 1
                break
    else:
        raise RuntimeError("Could not find end of __redoc_state JSON")

    redoc_state = json.loads(html[json_start:json_end].strip())

    # Navigate to the actual spec
    spec = None
    if "spec" in redoc_state and isinstance(redoc_state["spec"], dict):
        spec = redoc_state["spec"].get("data")
    if spec is None and "definition" in redoc_state:
        spec = redoc_state["definition"]
    if spec is None and "openapi" in redoc_state:
        spec = redoc_state

    if spec is None or "openapi" not in spec:
        raise RuntimeError("Could not locate OpenAPI spec in __redoc_state")

    path_count = len(spec.get("paths", {}))
    print(f"      OpenAPI {spec['openapi']}, {path_count} paths")
    return spec


# ═══════════════════════════════════════════════════════════════════════
#  STEP 2: Compare with existing spec
# ═══════════════════════════════════════════════════════════════════════

def spec_hash(spec: dict) -> str:
    """Deterministic hash of the spec (ignoring whitespace formatting)."""
    raw = json.dumps(spec, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def compare_specs(new_spec: dict) -> dict:
    """Compare new spec against saved one. Returns a diff summary."""
    print("[3/5] Comparing with existing spec ...")

    if not os.path.exists(SPEC_PATH):
        print("      No existing spec found — first run")
        return {"changed": True, "reason": "first_run", "added": 0, "removed": 0, "modified": 0}

    with open(SPEC_PATH, "r", encoding="utf-8") as f:
        old_spec = json.load(f)

    old_hash = spec_hash(old_spec)
    new_hash = spec_hash(new_spec)

    if old_hash == new_hash:
        print("      Specs are identical (no changes)")
        return {"changed": False}

    # Detailed diff on paths
    old_paths = set()
    for path, methods in old_spec.get("paths", {}).items():
        for method in methods:
            if method in ("get", "post", "put", "patch", "delete"):
                old_paths.add(f"{method.upper()} {path}")

    new_paths = set()
    for path, methods in new_spec.get("paths", {}).items():
        for method in methods:
            if method in ("get", "post", "put", "patch", "delete"):
                new_paths.add(f"{method.upper()} {path}")

    added = new_paths - old_paths
    removed = old_paths - new_paths
    # For modified — same path but potentially different schemas/params
    common = old_paths & new_paths

    print(f"      Changes detected!")
    print(f"      + {len(added)} new endpoints")
    print(f"      - {len(removed)} removed endpoints")
    print(f"      ~ {len(common)} endpoints (may have parameter changes)")

    if added:
        for ep in sorted(added)[:10]:
            print(f"        + {ep}")
        if len(added) > 10:
            print(f"        ... and {len(added) - 10} more")

    if removed:
        for ep in sorted(removed)[:10]:
            print(f"        - {ep}")
        if len(removed) > 10:
            print(f"        ... and {len(removed) - 10} more")

    return {
        "changed": True,
        "reason": "spec_changed",
        "added": len(added),
        "removed": len(removed),
        "modified": 0,  # detailed field-level diff is expensive, skip
    }


# ═══════════════════════════════════════════════════════════════════════
#  STEP 3: Build tag_endpoints.json from spec
# ═══════════════════════════════════════════════════════════════════════

def build_tag_endpoints(spec: dict) -> dict:
    """Group all endpoints by their tag."""
    tag_endpoints: dict[str, list] = {}
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            tags = details.get("tags", ["Untagged"])
            for tag in tags:
                tag_endpoints.setdefault(tag, [])
                tag_endpoints[tag].append({
                    "method": method.upper(),
                    "path": path,
                    "summary": details.get("summary", details.get("operationId", "")),
                    "operationId": details.get("operationId", ""),
                    "security": details.get("security", []),
                })
    return tag_endpoints


# ═══════════════════════════════════════════════════════════════════════
#  STEP 4: Generate tool modules (same logic as generate_tools_v2.py)
# ═══════════════════════════════════════════════════════════════════════

TAG_TO_MODULE = {
    "Авторизация": "auth",
    "Онлайн-запись": "booking", "Записи пользователя": "booking",
    "Пользователи онлайн-записи": "booking",
    "Компании": "companies", "Пользователи компании": "companies",
    "Категория услуг": "services", "Услуги": "services",
    "Сотрудники": "staff", "Должности": "staff", "Расчёт зарплат": "staff",
    "Клиенты": "clients", "Сетевые клиенты": "clients",
    "Записи": "records", "Визиты": "records",
    "Групповые события": "group_events", "Групповые события v2": "group_events",
    "Расписания записей/событий": "schedule", "График работы сотрудника": "schedule",
    "Даты для журнала": "schedule", "Сеансы для журнала": "schedule",
    "Лист ожидания": "schedule",
    "Комментарии": "comments",
    "Пользователи": "users", "Пользователь": "users",
    "Кассы": "finances", "Финансовые транзакции": "finances",
    "ККМ транзакции": "finances", "Операция продажи": "finances",
    "Лояльность": "loyalty", "Карты лояльности": "loyalty",
    "Сертификаты": "loyalty", "Абонементы": "loyalty",
    "Применение лояльности в визите": "loyalty",
    "Товары": "products", "Категории товаров": "products",
    "Категории": "products", "Технологические карты и расходники": "products",
    "Склады": "inventory", "Складские операции": "inventory",
    "Документы складских операций": "inventory", "Товарные транзакции": "inventory",
    "SMS рассылка": "communications", "Email рассылка": "communications",
    "Отправка СМС через операторов": "communications",
    "Аналитика": "analytics", "Z-Отчет": "analytics",
    "Справочники": "locations", "Страны": "locations", "Города": "locations",
    "Изображения": "images",
    "Сети салонов": "salon_chains",
    "Дополнительные поля": "custom_fields",
    "Отзывы и чаевые": "reviews",
    "Ресурсы": "resources",
    "Маркетплейс": "marketplace", "Интеграция с маркетплейсом": "marketplace",
    "Интеграция с сетевой телефонией": "telephony",
    "Фискализация чеков": "fiscalization",
    "Лицензии": "licenses",
    "Правила обработки персональных данных": "privacy",
    "Валидация данных": "validation_tools",
    "Личные счета": "personal_accounts",
    "Настройки уведомлений": "notifications", "Уведомления": "notifications",
    "Вебхуки": "webhooks", "Webhooks": "webhooks",
}

MODULE_DESC = {
    "auth": "Authentication — authorize users and get tokens",
    "booking": "Online booking — forms, dates, staff, services, sessions, user records",
    "companies": "Companies — list, get, create, update companies and company users",
    "services": "Services — manage service categories and individual services",
    "staff": "Staff — employees, positions, schedules, salary calculations",
    "clients": "Clients — manage, search, import clients and network clients",
    "records": "Records & Visits — manage appointment records and visit history",
    "group_events": "Group Events — create, update, delete group events and sessions",
    "schedule": "Schedule — staff schedules, journal dates/sessions, waiting list",
    "comments": "Comments — user comments on companies and staff",
    "users": "Users — manage users, roles, and permissions",
    "finances": "Finances — cash registers, transactions, KKM, sales operations",
    "loyalty": "Loyalty — programs, cards, certificates, subscriptions, visit loyalty",
    "products": "Products — goods, product categories, tech cards and consumables",
    "inventory": "Inventory — warehouses, operations, documents, goods transactions",
    "communications": "Communications — SMS campaigns, email campaigns, SMS providers",
    "analytics": "Analytics — company analytics and Z-reports",
    "locations": "Locations — countries, cities, business type directories",
    "images": "Images — manage images for companies and services",
    "salon_chains": "Salon Chains — manage salon chain networks",
    "custom_fields": "Custom Fields — custom fields for records and clients",
    "reviews": "Reviews — manage reviews and tips",
    "resources": "Resources — manage booking resources",
    "marketplace": "Marketplace — marketplace integrations and webhooks",
    "telephony": "Telephony — network telephony integration",
    "fiscalization": "Fiscalization — receipt fiscalization for partners",
    "licenses": "Licenses — manage company licenses",
    "privacy": "Privacy — personal data processing rules",
    "validation_tools": "Validation — data validation helpers",
    "personal_accounts": "Personal Accounts — manage personal client accounts",
    "notifications": "Notifications — notification settings",
    "webhooks": "Webhooks — manage webhook subscriptions",
    "misc": "Miscellaneous — other API operations",
}


def _make_english_name(method: str, path: str, summary: str, seen: set[str]) -> str:
    method_l = method.lower()
    clean = re.sub(r"^/api/v\d+/", "", path).rstrip("/")
    clean = re.sub(r"\{[^}]+\}", "", clean)
    clean = re.sub(r"/+", "/", clean).strip("/")
    parts = [p for p in clean.split("/") if p]

    slug = "_".join(parts[-2:]) if len(parts) >= 2 else (parts[0] if parts else "call")
    slug = re.sub(r"[^a-zA-Z0-9_]", "_", slug).strip("_").lower()

    verb_map = {"get": "get", "post": "create", "put": "update", "patch": "patch", "delete": "delete"}
    verb = verb_map.get(method_l, method_l)

    sl = summary.lower()
    if method_l == "get" and ("список" in sl or "list" in sl):
        verb = "list"
    elif method_l == "post" and ("поиск" in sl or "search" in sl):
        verb = "search"
    elif method_l == "post" and ("отправить" in sl or "send" in sl):
        verb = "send"
    elif method_l == "post" and ("авторизовать" in sl or "auth" in sl):
        verb = "auth"
    elif method_l == "get" and "получить" in sl and "список" not in sl:
        verb = "get"

    name = f"{verb}_{slug}"[:50].rstrip("_")

    base, i = name, 2
    while name in seen:
        name = f"{base}_{i}"
        i += 1
    seen.add(name)
    return name


def _needs_user_auth(security: list) -> bool:
    for sec in security:
        if "user" in sec or "BearerPartnerUser" in sec:
            return True
    return False


def generate_tools(tag_endpoints: dict) -> int:
    """Generate all tool modules. Returns total operation count."""
    print("[4/5] Generating tool modules ...")

    module_data: dict[str, list] = {}
    for tag, endpoints in tag_endpoints.items():
        mod = TAG_TO_MODULE.get(tag, "misc")
        module_data.setdefault(mod, [])
        for ep in endpoints:
            ep["_tag"] = tag
            module_data[mod].append(ep)

    generated: list[str] = []
    total_ops = 0

    for mod_name, endpoints in sorted(module_data.items()):
        seen: set[str] = set()
        ops = []
        for ep in endpoints:
            op_name = _make_english_name(ep["method"], ep["path"], ep["summary"], seen)
            ops.append({
                "name": op_name,
                "method": ep["method"],
                "path": ep["path"],
                "summary": ep["summary"],
                "needs_user": _needs_user_auth(ep["security"]),
            })

        desc = MODULE_DESC.get(mod_name, f"YCLIENTS {mod_name} operations")
        tool_name = f"yclients_{mod_name}"

        doc_lines = [f"  - {o['name']}: [{o['method']}] {o['summary']}" for o in ops]
        ops_doc = "\n".join(doc_lines)

        ops_dict_lines = [f'    "{o["name"]}": ("{o["method"]}", "{o["path"]}", {o["needs_user"]}),' for o in ops]
        ops_dict_str = "\n".join(ops_dict_lines)

        code = f'''"""YCLIENTS MCP tools: {desc}"""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..client import YClientsClient, _build_path


# (operation_name) -> (HTTP_METHOD, path_template, needs_user_token)
OPERATIONS: dict[str, tuple[str, str, bool]] = {{
{ops_dict_str}
}}


def register(mcp: FastMCP, client: YClientsClient) -> None:
    @mcp.tool()
    async def {tool_name}(operation: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """{desc}

Available operations:
{ops_doc}

Args:
    operation: One of the operation names listed above.
    params: Dict with keys depending on the operation:
        - Path parameters (e.g. company_id, record_id) — used to fill URL placeholders.
        - "query" — dict of query-string parameters.
        - "body" — dict for the JSON request body (POST/PUT/PATCH).
"""
        if operation not in OPERATIONS:
            return {{
                "error": True,
                "message": f"Unknown operation '{{operation}}'. Available: {{', '.join(sorted(OPERATIONS))}}"
            }}

        method, path_template, needs_user = OPERATIONS[operation]
        p = params or {{}}

        try:
            path = _build_path(path_template, p)
        except ValueError as exc:
            return {{"error": True, "message": f"Missing required path parameter: {{exc}}"}}

        return await client.request(
            method=method,
            path=path,
            needs_user_token=needs_user,
            query=p.get("query"),
            body=p.get("body"),
        )
'''
        filepath = os.path.join(TOOLS_DIR, f"{mod_name}.py")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(code)
        generated.append(mod_name)
        total_ops += len(ops)

    # Generate __init__.py
    imports = [f"from . import {m}" for m in sorted(generated)]
    registers = [f"    {m}.register(mcp, client)" for m in sorted(generated)]

    init_code = f'''"""Auto-generated: registers all YCLIENTS tool modules."""
from __future__ import annotations

from fastmcp import FastMCP

from ..client import YClientsClient

{chr(10).join(imports)}


def register_all_tools(mcp: FastMCP, client: YClientsClient) -> None:
{chr(10).join(registers)}
'''
    with open(os.path.join(TOOLS_DIR, "__init__.py"), "w", encoding="utf-8") as f:
        f.write(init_code)

    print(f"      Generated {len(generated)} modules, {total_ops} operations")
    return total_ops


# ═══════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════

def main() -> int:
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    print("=" * 60)
    print("YCLIENTS MCP Server — Spec Sync")
    print("=" * 60)

    # Step 1: Download
    html = download_html(YCLIENTS_DOC_URL)

    # Step 2: Extract
    new_spec = extract_spec_from_html(html)

    # Step 3: Compare
    diff = compare_specs(new_spec)

    if not diff["changed"] and not force:
        print("\n[OK] No changes detected. Nothing to do.")
        return 0

    if dry_run:
        print("\n[DRY-RUN] Changes detected but --dry-run specified. Exiting.")
        return 2

    # Step 4: Save new spec & tag_endpoints
    print("[5/5] Saving updated spec and regenerating tools ...")
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(SPEC_PATH, "w", encoding="utf-8") as f:
        json.dump(new_spec, f, ensure_ascii=False, indent=2)

    tag_endpoints = build_tag_endpoints(new_spec)
    with open(TAG_ENDPOINTS_PATH, "w", encoding="utf-8") as f:
        json.dump(tag_endpoints, f, ensure_ascii=False, indent=2)

    # Step 5: Generate tools
    total = generate_tools(tag_endpoints)

    print()
    print("=" * 60)
    reason = "forced" if force and not diff["changed"] else diff.get("reason", "updated")
    print(f"[DONE] Spec synced ({reason}). {total} operations ready.")
    print("       Restart the MCP server to apply changes.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
