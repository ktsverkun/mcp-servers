from __future__ import annotations

import logging
import os


def setup_logging() -> None:
    level = os.environ.get("MCP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class YClientsConfig:
    """Configuration loaded from environment variables."""

    def __init__(self) -> None:
        self.partner_token: str = os.environ.get("YCLIENTS_PARTNER_TOKEN", "")
        self.user_token: str = os.environ.get("YCLIENTS_USER_TOKEN", "")
        self.base_url: str = os.environ.get("YCLIENTS_BASE_URL", "https://api.yclients.com")

        if not self.partner_token:
            logging.getLogger(__name__).warning(
                "YCLIENTS_PARTNER_TOKEN is not set. "
                "API calls to YClients will fail without a valid partner token."
            )
