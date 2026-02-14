"""YCLIENTS MCP Server — exposes the full YCLIENTS REST API as grouped MCP tools."""

from __future__ import annotations

import json
import os

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

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


@mcp.custom_route("/", methods=["GET"])
async def server_info(request: Request) -> JSONResponse:
    """Discovery endpoint — returns server info with tools list (like Ozon)."""
    tools = []
    for tool in mcp._tool_manager._tools.values():
        tools.append({
            "name": tool.name,
            "description": tool.description or "",
        })
    return JSONResponse({
        "name": "YCLIENTS MCP Server",
        "version": "2.14.5",
        "description": (
            "MCP Server for YCLIENTS CRM — booking, clients, staff, services, "
            "finances, loyalty, inventory, analytics and more"
        ),
        "endpoints": {
            "/mcp": "MCP Streamable HTTP endpoint (POST/GET/DELETE)",
            "/health": "Health check",
        },
        "tools": tools,
    })


def main() -> None:
    setup_logging()
    transport = os.environ.get("MCP_TRANSPORT", "stdio")  # "stdio" or "http"
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = int(os.environ.get("MCP_PORT", "8000"))

    if transport == "http":
        mcp.run(transport="http", host=host, port=port, json_response=True, stateless_http=True)
    else:
        mcp.run()  # stdio — default for local Claude Desktop


if __name__ == "__main__":
    main()
