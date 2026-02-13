from __future__ import annotations

import os

import pytest

# Set test tokens so config doesn't crash
os.environ.setdefault("YCLIENTS_PARTNER_TOKEN", "test_partner_token")
os.environ.setdefault("YCLIENTS_USER_TOKEN", "test_user_token")


@pytest.fixture()
def config():
    from yclients_mcp.config import YClientsConfig

    return YClientsConfig()


@pytest.fixture()
def client(config):
    from yclients_mcp.client import YClientsClient

    return YClientsClient(config)
