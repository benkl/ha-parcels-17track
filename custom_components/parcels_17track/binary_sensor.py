"""Binary sensor: a parcel is out for delivery today."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import ParcelCoordinator
from .entity import ParcelEntity
from .parcels import STATE_OUT_FOR_DELIVERY


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([DeliveryTodaySensor(entry.runtime_data)])


class DeliveryTodaySensor(ParcelEntity, BinarySensorEntity):
    def __init__(self, coordinator: ParcelCoordinator) -> None:
        super().__init__(coordinator, "delivery_today")

    def _today(self) -> list[dict[str, Any]]:
        return [p for p in self.coordinator.data["parcels"] if p["state"] == STATE_OUT_FOR_DELIVERY]

    @property
    def is_on(self) -> bool:
        return bool(self._today())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"parcels": [p["name"] for p in self._today()]}
