from __future__ import annotations

from .config import YClientsConfig


def build_headers(config: YClientsConfig, needs_user_token: bool = True) -> dict[str, str]:
    """Build request headers with appropriate auth tokens.

    The YCLIENTS API uses two tokens:
    - Partner token (Bearer) — always required
    - User token — required for most data-mutating and company-scoped operations
    """
    headers: dict[str, str] = {
        "Accept": "application/vnd.yclients.v2+json",
        "Content-Type": "application/json",
    }

    if needs_user_token and config.user_token:
        headers["Authorization"] = f"Bearer {config.partner_token}, User {config.user_token}"
    else:
        headers["Authorization"] = f"Bearer {config.partner_token}"

    return headers
