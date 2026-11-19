"""Parcels for 17TRACK – parcel overview, notifications and dashboard card on top of the 17TRACK integration."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.typing import ConfigType

from .const import (
    ARCHIVE_HOUR,
    CARD_FILE,
    CONF_SOURCE_ENTRY,
    DOMAIN,
    FRONTEND_URL,
    VERSION,
)
from .coordinator import ParcelCoordinator
from .services import async_setup_services

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register services and the dashboard card once."""
    async_setup_services(hass)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(Path(__file__).parent / "frontend"), False)]
    )
    add_extra_js_url(hass, f"{FRONTEND_URL}/{CARD_FILE}?v={VERSION}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one 17TRACK account."""
    source = hass.config_entries.async_get_entry(entry.data[CONF_SOURCE_ENTRY])
    if source is None:
        raise ConfigEntryError("The linked 17TRACK integration entry no longer exists")
    if source.state is not ConfigEntryState.LOADED:
        raise ConfigEntryNotReady("Waiting for the 17TRACK integration to load")

    coordinator = ParcelCoordinator(hass, entry)
    await coordinator.async_load_snapshot()
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    entry.async_on_unload(
        async_track_time_change(hass, coordinator.async_auto_archive, hour=ARCHIVE_HOUR, minute=0, second=0)
    )
    entry.async_on_unload(entry.add_update_listener(_async_reload_on_options))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_reload_on_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
