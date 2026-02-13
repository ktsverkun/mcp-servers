"""YCLIENTS MCP Server — exposes the full YCLIENTS REST API as grouped MCP tools."""

from __future__ import annotations

import os

from fastmcp import FastMCP

from .client import BookingClient, YClientsClient
from .config import YClientsConfig, setup_logging
from .tools import register_all_tools

mcp = FastMCP(
    "yclients",
    instructions=(
        "YCLIENTS MCP Server provides access to the full YCLIENTS REST API "
        "(304 endpoints). Tools are grouped by domain: booking, clients, staff, "
        "services, finances, loyalty, inventory, analytics, etc. "
        "Each tool accepts an 'operation' parameter to select the specific API call, "
        "and a 'params' dict for path/query/body parameters."
    ),
)

config = YClientsConfig()
client = YClientsClient(config)
booking_client = BookingClient(config.partner_token)
register_all_tools(mcp, client, booking_client)


def main() -> None:
    setup_logging()
    transport = os.environ.get("MCP_TRANSPORT", "stdio")  # "stdio" or "http"
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))

    if transport == "http":
        mcp.run(transport="http", host=host, port=port)
    else:
        mcp.run()  # stdio — default for local Claude Desktop


if __name__ == "__main__":
    main()
