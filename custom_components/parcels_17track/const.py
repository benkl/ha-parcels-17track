"""Constants for Parcels for 17TRACK."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "parcels_17track"
SOURCE_DOMAIN: Final = "seventeentrack"
VERSION: Final = "1.0.0"

# Config entry data / options
CONF_SOURCE_ENTRY: Final = "source_entry_id"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_NOTIFY_TARGETS: Final = "notify_targets"
CONF_NOTIFY_EVENTS: Final = "notify_events"
CONF_ARCHIVE_DAYS: Final = "archive_after_days"
CONF_KEYWORDS: Final = "out_for_delivery_keywords"

# Notification event types (also used as option values)
EVENT_NEW: Final = "new"
EVENT_IN_TRANSIT: Final = "in_transit"
EVENT_OUT_FOR_DELIVERY: Final = "out_for_delivery"
EVENT_READY_FOR_PICKUP: Final = "ready_for_pickup"
EVENT_DELIVERED: Final = "delivered"
EVENT_PROBLEM: Final = "problem"
NOTIFY_EVENTS: Final = [
    EVENT_NEW,
    EVENT_IN_TRANSIT,
    EVENT_OUT_FOR_DELIVERY,
    EVENT_READY_FOR_PICKUP,
    EVENT_DELIVERED,
    EVENT_PROBLEM,
]

DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_ARCHIVE_DAYS: Final = 3
DEFAULT_KEYWORDS: Final = (
    "out for delivery, in delivery, in zustellung, zur zustellung, "
    "zustellfahrzeug, wird heute zugestellt, en cours de livraison, "
    "in consegna, en reparto, wordt vandaag bezorgd"
)
DEFAULT_OPTIONS: Final = {
    CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    CONF_NOTIFY_TARGETS: [],
    CONF_NOTIFY_EVENTS: list(NOTIFY_EVENTS),
    CONF_ARCHIVE_DAYS: DEFAULT_ARCHIVE_DAYS,
    CONF_KEYWORDS: DEFAULT_KEYWORDS,
}

# Bus event fired for every detected change (for user automations)
BUS_EVENT_CHANGED: Final = f"{DOMAIN}_changed"

# Services
SERVICE_ADD_PARCEL: Final = "add_parcel"
SERVICE_ARCHIVE_PARCEL: Final = "archive_parcel"
SERVICE_REFRESH: Final = "refresh"
ATTR_TRACKING_NUMBER: Final = "tracking_number"
ATTR_NAME: Final = "name"
ATTR_CONFIG_ENTRY_ID: Final = "config_entry_id"

# Frontend
FRONTEND_URL: Final = f"/{DOMAIN}"
CARD_FILE: Final = "parcels-17track-card.js"

STORAGE_VERSION: Final = 1
ARCHIVE_HOUR: Final = 4
ADD_REFRESH_DELAY: Final = 15
