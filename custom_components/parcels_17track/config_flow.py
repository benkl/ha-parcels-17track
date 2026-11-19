"""Config and options flow."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
)

from .const import (
    CONF_ARCHIVE_DAYS,
    CONF_KEYWORDS,
    CONF_NOTIFY_EVENTS,
    CONF_NOTIFY_TARGETS,
    CONF_SCAN_INTERVAL,
    CONF_SOURCE_ENTRY,
    DEFAULT_OPTIONS,
    DOMAIN,
    NOTIFY_EVENTS,
    SOURCE_DOMAIN,
)

try:  # Home Assistant 2026+ validates with probatio, older releases with voluptuous
    import probatio as vol
except ImportError:  # pragma: no cover
    import voluptuous as vol


class ParcelsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Link a 17TRACK account."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        sources = self.hass.config_entries.async_entries(SOURCE_DOMAIN)
        if not sources:
            return self.async_abort(reason="no_source")

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SOURCE_ENTRY])
            self._abort_if_unique_id_configured()
            source = self.hass.config_entries.async_get_entry(user_input[CONF_SOURCE_ENTRY])
            return self.async_create_entry(
                title=f"17TRACK {source.title}" if source else "17TRACK",
                data={CONF_SOURCE_ENTRY: user_input[CONF_SOURCE_ENTRY]},
                options=dict(DEFAULT_OPTIONS),
            )

        options = [SelectOptionDict(value=e.entry_id, label=e.title) for e in sources]
        schema = vol.Schema(
            {
                vol.Required(CONF_SOURCE_ENTRY, default=options[0]["value"]): SelectSelector(
                    SelectSelectorConfig(options=options, mode=SelectSelectorMode.DROPDOWN)
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return ParcelsOptionsFlow()


class ParcelsOptionsFlow(OptionsFlow):
    """Refresh interval, notifications, auto-archive, keywords."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            user_input[CONF_SCAN_INTERVAL] = int(user_input[CONF_SCAN_INTERVAL])
            user_input[CONF_ARCHIVE_DAYS] = int(user_input[CONF_ARCHIVE_DAYS])
            return self.async_create_entry(data=user_input)

        opts = {**DEFAULT_OPTIONS, **self.config_entry.options}
        notify = sorted(f"notify.{name}" for name in self.hass.services.async_services().get("notify", {}))
        notify = [n for n in notify if n != "notify.send_message"]

        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=opts[CONF_SCAN_INTERVAL]): NumberSelector(
                    NumberSelectorConfig(min=5, max=360, step=5, unit_of_measurement="min", mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_NOTIFY_TARGETS, default=opts[CONF_NOTIFY_TARGETS]): SelectSelector(
                    SelectSelectorConfig(
                        options=notify, multiple=True, custom_value=True, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(CONF_NOTIFY_EVENTS, default=opts[CONF_NOTIFY_EVENTS]): SelectSelector(
                    SelectSelectorConfig(
                        options=NOTIFY_EVENTS,
                        multiple=True,
                        mode=SelectSelectorMode.LIST,
                        translation_key=CONF_NOTIFY_EVENTS,
                    )
                ),
                vol.Required(CONF_ARCHIVE_DAYS, default=opts[CONF_ARCHIVE_DAYS]): NumberSelector(
                    NumberSelectorConfig(min=0, max=60, step=1, unit_of_measurement="d", mode=NumberSelectorMode.BOX)
                ),
                vol.Optional(CONF_KEYWORDS, default=opts[CONF_KEYWORDS]): TextSelector(
                    TextSelectorConfig(multiline=True)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
