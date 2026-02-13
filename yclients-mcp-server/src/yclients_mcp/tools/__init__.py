"""Auto-generated: registers all YCLIENTS tool modules."""

from __future__ import annotations

from fastmcp import FastMCP

from ..client import BookingClient, YClientsClient
from . import (
    analytics,
    auth,
    booking,
    client_booking,
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


def register_all_tools(mcp: FastMCP, client: YClientsClient, booking_client: BookingClient | None = None) -> None:
    analytics.register(mcp, client)
    auth.register(mcp, client)
    booking.register(mcp, client)
    if booking_client is not None:
        client_booking.register(mcp, booking_client)
    clients.register(mcp, client)
    comments.register(mcp, client)
    communications.register(mcp, client)
    companies.register(mcp, client)
    custom_fields.register(mcp, client)
    finances.register(mcp, client)
    fiscalization.register(mcp, client)
    group_events.register(mcp, client)
    images.register(mcp, client)
    inventory.register(mcp, client)
    licenses.register(mcp, client)
    locations.register(mcp, client)
    loyalty.register(mcp, client)
    marketplace.register(mcp, client)
    misc.register(mcp, client)
    notifications.register(mcp, client)
    personal_accounts.register(mcp, client)
    privacy.register(mcp, client)
    products.register(mcp, client)
    records.register(mcp, client)
    resources.register(mcp, client)
    reviews.register(mcp, client)
    salon_chains.register(mcp, client)
    schedule.register(mcp, client)
    services.register(mcp, client)
    staff.register(mcp, client)
    telephony.register(mcp, client)
    users.register(mcp, client)
    validation_tools.register(mcp, client)
