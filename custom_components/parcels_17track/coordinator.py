"""Data coordinator: polls 17TRACK via the core integration and reacts to changes."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from . import parcels as pl
from .const import (
    BUS_EVENT_CHANGED,
    CONF_ARCHIVE_DAYS,
    CONF_KEYWORDS,
    CONF_NOTIFY_EVENTS,
    CONF_NOTIFY_TARGETS,
    CONF_SCAN_INTERVAL,
    CONF_SOURCE_ENTRY,
    DEFAULT_OPTIONS,
    DOMAIN,
    SOURCE_DOMAIN,
    STORAGE_VERSION,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


class ParcelCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches parcels, keeps a persisted snapshot and sends notifications."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.options: dict[str, Any] = {**DEFAULT_OPTIONS, **entry.options}
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=int(self.options[CONF_SCAN_INTERVAL])),
        )
        self.source_entry_id: str = entry.data[CONF_SOURCE_ENTRY]
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
        self._snapshot: dict[str, dict[str, Any]] | None = None

    @property
    def lang(self) -> str:
        return pl.language(self.hass.config.language)

    async def async_load_snapshot(self) -> None:
        """Load the last known parcel states (so restarts don't miss or repeat changes)."""
        stored = await self._store.async_load()
        self._snapshot = stored.get("snapshot") if stored else None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            response = await self.hass.services.async_call(
                SOURCE_DOMAIN,
                "get_packages",
                {"config_entry_id": self.source_entry_id},
                blocking=True,
                return_response=True,
            )
        except HomeAssistantError as err:
            raise UpdateFailed(f"17TRACK request failed: {err}") from err
        except Exception as err:  # noqa: BLE001 - library errors are not HomeAssistantErrors
            raise UpdateFailed(f"17TRACK not reachable: {err}") from err

        keywords = pl.parse_keywords(self.options[CONF_KEYWORDS])
        raw = (response or {}).get("packages", [])
        parcels = pl.sort_parcels(pl.normalize(p, keywords, self.lang) for p in raw)

        changes = pl.diff(self._snapshot, parcels)
        self._snapshot = pl.snapshot(parcels)
        await self._store.async_save({"snapshot": self._snapshot})
        if changes:
            self.config_entry.async_create_background_task(
                self.hass, self._async_handle_changes(changes), f"{DOMAIN} notifications"
            )

        return {
            "parcels": parcels,
            "counts": pl.counts(parcels),
            "last_success": dt_util.utcnow(),
        }

    async def _async_handle_changes(self, changes: list[dict[str, Any]]) -> None:
        """Fire bus events and push notifications for detected changes."""
        targets: list[str] = list(self.options[CONF_NOTIFY_TARGETS] or [])
        wanted: set[str] = set(self.options[CONF_NOTIFY_EVENTS] or [])
        for change in changes:
            parcel = change["parcel"]
            self.hass.bus.async_fire(
                BUS_EVENT_CHANGED,
                {
                    "type": change["type"],
                    "previous_state": change["previous_state"],
                    "state": parcel["state"],
                    "tracking_number": parcel["tracking_number"],
                    "name": parcel["name"],
                    "info_text": parcel["info_text"],
                    "location": parcel["location"],
                    "url": parcel["url"],
                },
            )
            if change["type"] not in wanted:
                continue
            text = pl.message(change, self.lang)
            for target in targets:
                await self._async_notify(target, text, parcel)

    async def _async_notify(self, target: str, text: dict[str, str], parcel: dict[str, Any]) -> None:
        domain, _, service = target.partition(".")
        if not service:
            domain, service = "notify", target
        data: dict[str, Any] = {**text}
        if service.startswith("mobile_app_"):
            data["data"] = {
                "tag": f"{DOMAIN}_{parcel['tracking_number']}",
                "group": DOMAIN,
                "url": parcel["url"],
                "clickAction": parcel["url"],
                "notification_icon": "mdi:package-variant",
            }
        try:
            await self.hass.services.async_call(domain, service, data, blocking=True)
        except Exception as err:  # noqa: BLE001 - one broken target must not stop the others
            _LOGGER.warning("Could not notify %s: %s", target, err)

    async def async_auto_archive(self, now: datetime | None = None) -> None:
        """Archive parcels delivered more than N days ago."""
        days = int(self.options[CONF_ARCHIVE_DAYS] or 0)
        if not self.data or days <= 0:
            return
        numbers = pl.archive_candidates(self.data["parcels"], days, dt_util.utcnow())
        for number in numbers:
            try:
                await self.async_archive(number)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Could not archive %s: %s", number, err)
        if numbers:
            _LOGGER.info("Archived %d delivered parcel(s)", len(numbers))
            await self.async_request_refresh()

    async def async_add(self, number: str, name: str | None, context=None) -> None:
        await self.hass.services.async_call(
            SOURCE_DOMAIN,
            "add_package",
            {
                "config_entry_id": self.source_entry_id,
                "package_tracking_number": number,
                "package_friendly_name": name or number,
            },
            blocking=True,
            context=context,
        )

    async def async_archive(self, number: str, context=None) -> None:
        await self.hass.services.async_call(
            SOURCE_DOMAIN,
            "archive_package",
            {"config_entry_id": self.source_entry_id, "package_tracking_number": number},
            blocking=True,
            context=context,
        )
