"""Sensors: parcel overview (with full list) and per-group counts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SCAN_INTERVAL
from .coordinator import ParcelCoordinator
from .entity import ParcelEntity


@dataclass(frozen=True, kw_only=True)
class ParcelSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]


def _count(key: str) -> Callable[[dict[str, Any]], int]:
    return lambda data: data["counts"][key]


COUNT_SENSORS: tuple[ParcelSensorDescription, ...] = (
    ParcelSensorDescription(key="in_transit", state_class=SensorStateClass.MEASUREMENT, value_fn=_count("in_transit")),
    ParcelSensorDescription(
        key="out_for_delivery", state_class=SensorStateClass.MEASUREMENT, value_fn=_count("out_for_delivery")
    ),
    ParcelSensorDescription(
        key="ready_for_pickup", state_class=SensorStateClass.MEASUREMENT, value_fn=_count("ready_for_pickup")
    ),
    ParcelSensorDescription(key="delivered", state_class=SensorStateClass.MEASUREMENT, value_fn=_count("delivered")),
    ParcelSensorDescription(key="problems", state_class=SensorStateClass.MEASUREMENT, value_fn=_count("problems")),
    ParcelSensorDescription(
        key="last_update",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data["last_success"],
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: ParcelCoordinator = entry.runtime_data
    async_add_entities(
        [ParcelOverviewSensor(coordinator)] + [ParcelCountSensor(coordinator, d) for d in COUNT_SENSORS]
    )


class ParcelOverviewSensor(ParcelEntity, SensorEntity):
    """Number of open parcels; the full parcel list is in the attributes (used by the card)."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _unrecorded_attributes = frozenset({"parcels"})

    def __init__(self, coordinator: ParcelCoordinator) -> None:
        super().__init__(coordinator, "open")

    @property
    def native_value(self) -> int:
        return self.coordinator.data["counts"]["open"]

    @property
    def icon(self) -> str:
        return "mdi:truck-delivery-outline" if self.native_value else "mdi:package-variant-closed"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data
        return {
            "parcels": data["parcels"],
            **data["counts"],
            "last_success": data["last_success"].isoformat(),
            "scan_interval": int(self.coordinator.options[CONF_SCAN_INTERVAL]),
            "integration": "parcels_17track",
        }


class ParcelCountSensor(ParcelEntity, SensorEntity):
    entity_description: ParcelSensorDescription

    def __init__(self, coordinator: ParcelCoordinator, description: ParcelSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)
