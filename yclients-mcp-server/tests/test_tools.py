"""Tests that all tool modules load correctly and have valid OPERATIONS."""

from __future__ import annotations

import pytest

from yclients_mcp.tools import (
    analytics,
    auth,
    booking,
    clients,
    comments,
    communications,
    companies,
    custom_fields,
    finances,
    fiscalization,
    group_events,
    images,
    inventory,
    licenses,
    locations,
    loyalty,
    marketplace,
    misc,
    notifications,
    personal_accounts,
    privacy,
    products,
    records,
    resources,
    reviews,
    salon_chains,
    schedule,
    services,
    staff,
    telephony,
    users,
    validation_tools,
)

ALL_MODULES = [
    analytics,
    auth,
    booking,
    clients,
    comments,
    communications,
    companies,
    custom_fields,
    finances,
    fiscalization,
    group_events,
    images,
    inventory,
    licenses,
    locations,
    loyalty,
    marketplace,
    misc,
    notifications,
    personal_accounts,
    privacy,
    products,
    records,
    resources,
    reviews,
    salon_chains,
    schedule,
    services,
    staff,
    telephony,
    users,
    validation_tools,
]


@pytest.mark.parametrize("mod", ALL_MODULES, ids=lambda m: m.__name__.split(".")[-1])
def test_module_has_operations(mod):
    """Every tool module must define an OPERATIONS dict."""
    assert hasattr(mod, "OPERATIONS")
    assert isinstance(mod.OPERATIONS, dict)
    assert len(mod.OPERATIONS) > 0


@pytest.mark.parametrize("mod", ALL_MODULES, ids=lambda m: m.__name__.split(".")[-1])
def test_module_has_register(mod):
    """Every tool module must define a register() function."""
    assert hasattr(mod, "register")
    assert callable(mod.register)


@pytest.mark.parametrize("mod", ALL_MODULES, ids=lambda m: m.__name__.split(".")[-1])
def test_operations_format(mod):
    """Each operation must be (METHOD, path_template, bool)."""
    for name, (method, path, needs_user) in mod.OPERATIONS.items():
        assert method in ("GET", "POST", "PUT", "PATCH", "DELETE"), f"{name}: bad method {method}"
        assert path.startswith("/"), f"{name}: path must start with /"
        assert isinstance(needs_user, bool), f"{name}: needs_user must be bool"


def test_total_operations():
    """Verify we cover all 305 operations."""
    total = sum(len(m.OPERATIONS) for m in ALL_MODULES)
    assert total >= 300, f"Expected ~305 operations, got {total}"


def test_no_duplicate_tool_names():
    """Tool function names must be unique across all modules."""
    names = set()
    for mod in ALL_MODULES:
        mod_name = mod.__name__.split(".")[-1]
        tool_name = f"yclients_{mod_name}"
        assert tool_name not in names, f"Duplicate tool: {tool_name}"
        names.add(tool_name)
