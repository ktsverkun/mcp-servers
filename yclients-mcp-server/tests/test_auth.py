from __future__ import annotations

from yclients_mcp.auth import build_headers


def test_headers_with_user_token(config):
    headers = build_headers(config, needs_user_token=True)
    assert "Bearer test_partner_token, User test_user_token" in headers["Authorization"]
    assert headers["Accept"] == "application/vnd.yclients.v2+json"


def test_headers_without_user_token(config):
    headers = build_headers(config, needs_user_token=False)
    assert headers["Authorization"] == "Bearer test_partner_token"
    assert "User" not in headers["Authorization"]


def test_headers_user_needed_but_missing(monkeypatch):
    monkeypatch.setenv("YCLIENTS_USER_TOKEN", "")
    from yclients_mcp.config import YClientsConfig

    cfg = YClientsConfig()
    headers = build_headers(cfg, needs_user_token=True)
    # Falls back to partner-only when user token is empty
    assert headers["Authorization"] == "Bearer test_partner_token"
