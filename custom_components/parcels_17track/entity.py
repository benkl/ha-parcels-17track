"""Shared entity base."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import ParcelCoordinator


class ParcelEntity(CoordinatorEntity[ParcelCoordinator]):
    """Base entity bound to one 17TRACK account device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ParcelCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="17TRACK Parcels",
            manufacturer="17TRACK",
            model="Parcel overview",
            sw_version=VERSION,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://t.17track.net",
        )
