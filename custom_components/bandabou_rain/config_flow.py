"""Config flow for Bandabou Rain."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_NOTIFY_ON_RAIN,
    CONF_NOTIFY_SERVICE,
    CONF_RAIN_THRESHOLD_MM,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_NAME,
    DEFAULT_NOTIFY_ON_RAIN,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_RAIN_THRESHOLD_MM,
    DOMAIN,
)


def _entry_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Return the config or options schema."""
    return vol.Schema(
        {
            vol.Optional(CONF_NAME, default=defaults[CONF_NAME]): str,
            vol.Optional(CONF_LATITUDE, default=defaults[CONF_LATITUDE]): vol.All(
                vol.Coerce(float), vol.Range(min=-90, max=90)
            ),
            vol.Optional(CONF_LONGITUDE, default=defaults[CONF_LONGITUDE]): vol.All(
                vol.Coerce(float), vol.Range(min=-180, max=180)
            ),
            vol.Optional(
                CONF_RAIN_THRESHOLD_MM,
                default=defaults[CONF_RAIN_THRESHOLD_MM],
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=5)),
            vol.Optional(
                CONF_NOTIFY_ON_RAIN,
                default=defaults[CONF_NOTIFY_ON_RAIN],
            ): bool,
            vol.Optional(
                CONF_NOTIFY_SERVICE,
                default=defaults[CONF_NOTIFY_SERVICE],
            ): str,
        }
    )


class BandabouRainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bandabou Rain."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> BandabouRainOptionsFlow:
        """Create the options flow."""
        return BandabouRainOptionsFlow(config_entry)

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            latitude = float(user_input[CONF_LATITUDE])
            longitude = float(user_input[CONF_LONGITUDE])
            await self.async_set_unique_id(f"{latitude:.5f}_{longitude:.5f}")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        defaults = {
            CONF_NAME: DEFAULT_NAME,
            CONF_LATITUDE: DEFAULT_LATITUDE,
            CONF_LONGITUDE: DEFAULT_LONGITUDE,
            CONF_RAIN_THRESHOLD_MM: DEFAULT_RAIN_THRESHOLD_MM,
            CONF_NOTIFY_ON_RAIN: DEFAULT_NOTIFY_ON_RAIN,
            CONF_NOTIFY_SERVICE: DEFAULT_NOTIFY_SERVICE,
        }
        return self.async_show_form(
            step_id="user",
            data_schema=_entry_schema(defaults),
        )


class BandabouRainOptionsFlow(config_entries.OptionsFlow):
    """Handle Bandabou Rain options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self._config_entry.data
        options = self._config_entry.options
        defaults = {
            CONF_NAME: options.get(CONF_NAME, data.get(CONF_NAME, DEFAULT_NAME)),
            CONF_LATITUDE: options.get(
                CONF_LATITUDE,
                data.get(CONF_LATITUDE, DEFAULT_LATITUDE),
            ),
            CONF_LONGITUDE: options.get(
                CONF_LONGITUDE,
                data.get(CONF_LONGITUDE, DEFAULT_LONGITUDE),
            ),
            CONF_RAIN_THRESHOLD_MM: options.get(
                CONF_RAIN_THRESHOLD_MM,
                data.get(CONF_RAIN_THRESHOLD_MM, DEFAULT_RAIN_THRESHOLD_MM),
            ),
            CONF_NOTIFY_ON_RAIN: options.get(
                CONF_NOTIFY_ON_RAIN,
                data.get(CONF_NOTIFY_ON_RAIN, DEFAULT_NOTIFY_ON_RAIN),
            ),
            CONF_NOTIFY_SERVICE: options.get(
                CONF_NOTIFY_SERVICE,
                data.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
            ),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=_entry_schema(defaults),
        )
