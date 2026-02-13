from __future__ import annotations

import httpx
import pytest
import respx

from yclients_mcp.client import _build_path

# ── _build_path tests ───────────────────────────────────────────────────


def test_build_path_simple():
    path = _build_path("/api/v1/company/{company_id}", {"company_id": 123})
    assert path == "/api/v1/company/123"


def test_build_path_multiple_params():
    path = _build_path(
        "/api/v1/client/{company_id}/{id}",
        {"company_id": 100, "id": 42},
    )
    assert path == "/api/v1/client/100/42"


def test_build_path_url_encodes_values():
    path = _build_path("/api/v1/i18n/{langCode}", {"langCode": "en/US"})
    assert "en%2FUS" in path
    assert "{" not in path


def test_build_path_missing_param():
    with pytest.raises(ValueError, match="company_id"):
        _build_path("/api/v1/company/{company_id}", {})


def test_build_path_no_placeholders():
    path = _build_path("/api/v1/auth", {"extra": "ignored"})
    assert path == "/api/v1/auth"


# ── YClientsClient tests ───────────────────────────────────────────────


@respx.mock
async def test_client_get_success(client):
    respx.get("https://api.yclients.com/api/v1/companies").mock(
        return_value=httpx.Response(200, json={"success": True, "data": []})
    )
    result = await client.request("GET", "/api/v1/companies")
    assert result["success"] is True


@respx.mock
async def test_client_handles_404(client):
    respx.get("https://api.yclients.com/api/v1/missing").mock(
        return_value=httpx.Response(404, json={"success": False, "message": "Not found"})
    )
    result = await client.request("GET", "/api/v1/missing")
    assert result["error"] is True
    assert result["status_code"] == 404


@respx.mock
async def test_client_handles_timeout(client):
    respx.get("https://api.yclients.com/api/v1/slow").mock(
        side_effect=httpx.TimeoutException("timed out")
    )
    result = await client.request("GET", "/api/v1/slow")
    assert result["error"] is True
    assert "timed out" in result["message"]
