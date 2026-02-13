from __future__ import annotations

import pytest


def test_config_loads_tokens(config):
    assert config.partner_token == "test_partner_token"
    assert config.user_token == "test_user_token"
    assert config.base_url == "https://api.yclients.com"


def test_config_requires_partner_token(monkeypatch):
    monkeypatch.delenv("YCLIENTS_PARTNER_TOKEN", raising=False)
    from yclients_mcp.config import YClientsConfig

    with pytest.raises(RuntimeError, match="YCLIENTS_PARTNER_TOKEN"):
        YClientsConfig()


def test_config_custom_base_url(monkeypatch):
    monkeypatch.setenv("YCLIENTS_BASE_URL", "https://custom.api.com")
    from yclients_mcp.config import YClientsConfig

    cfg = YClientsConfig()
    assert cfg.base_url == "https://custom.api.com"
