"""Services: add_parcel, archive_parcel, refresh."""

from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import (
    ADD_REFRESH_DELAY,
    ATTR_CONFIG_ENTRY_ID,
    ATTR_NAME,
    ATTR_TRACKING_NUMBER,
    DOMAIN,
    SERVICE_ADD_PARCEL,
    SERVICE_ARCHIVE_PARCEL,
    SERVICE_REFRESH,
)
from .coordinator import ParcelCoordinator

try:  # Home Assistant 2026+ validates with probatio, older releases with voluptuous
    import probatio as vol
except ImportError:  # pragma: no cover
    import voluptuous as vol

ADD_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TRACKING_NUMBER): cv.string,
        vol.Optional(ATTR_NAME): cv.string,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)
ARCHIVE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TRACKING_NUMBER): cv.string,
        vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string,
    }
)
REFRESH_SCHEMA = vol.Schema({vol.Optional(ATTR_CONFIG_ENTRY_ID): cv.string})


def _coordinator(hass: HomeAssistant, call: ServiceCall) -> ParcelCoordinator:
    wanted = call.data.get(ATTR_CONFIG_ENTRY_ID)
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED and (wanted is None or entry.entry_id == wanted):
            return entry.runtime_data
    raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_entry")


def _clean(number: str) -> str:
    return "".join(number.split()).upper()


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    async def add_parcel(call: ServiceCall) -> None:
        coordinator = _coordinator(hass, call)
        number = _clean(call.data[ATTR_TRACKING_NUMBER])
        if len(number) < 5:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="invalid_number")
        await coordinator.async_add(number, (call.data.get(ATTR_NAME) or "").strip() or None, call.context)

        async def _later() -> None:
            await asyncio.sleep(ADD_REFRESH_DELAY)  # 17TRACK needs a moment before it knows the parcel
            await coordinator.async_request_refresh()

        coordinator.config_entry.async_create_background_task(hass, _later(), f"{DOMAIN} refresh after add")

    async def archive_parcel(call: ServiceCall) -> None:
        coordinator = _coordinator(hass, call)
        await coordinator.async_archive(_clean(call.data[ATTR_TRACKING_NUMBER]), call.context)
        await coordinator.async_request_refresh()

    async def refresh(call: ServiceCall) -> None:
        await _coordinator(hass, call).async_refresh()

    hass.services.async_register(DOMAIN, SERVICE_ADD_PARCEL, add_parcel, schema=ADD_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_ARCHIVE_PARCEL, archive_parcel, schema=ARCHIVE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REFRESH, refresh, schema=REFRESH_SCHEMA)
