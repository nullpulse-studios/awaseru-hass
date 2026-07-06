"""Config flow for Bandabou Rain."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_DRY_DAY_THRESHOLD_MM,
    CONF_DRY_NOTIFY_COOLDOWN_MINUTES,
    CONF_DRY_NOTIFY_MESSAGE,
    CONF_DRY_NOTIFY_TITLE,
    CONF_DRY_STREAK_THRESHOLD_DAYS,
    CONF_NOTIFY_COOLDOWN_MINUTES,
    CONF_NOTIFY_MESSAGE,
    CONF_NOTIFY_ON_DRY_STREAK,
    CONF_NOTIFY_ON_RAIN,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_SERVICES,
    CONF_NOTIFY_TITLE,
    CONF_RAIN_THRESHOLD_MM,
    DEFAULT_DRY_DAY_THRESHOLD_MM,
    DEFAULT_DRY_NOTIFY_COOLDOWN_MINUTES,
    DEFAULT_DRY_NOTIFY_MESSAGE,
    DEFAULT_DRY_NOTIFY_TITLE,
    DEFAULT_DRY_STREAK_THRESHOLD_DAYS,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_NAME,
    DEFAULT_NOTIFY_COOLDOWN_MINUTES,
    DEFAULT_NOTIFY_MESSAGE,
    DEFAULT_NOTIFY_ON_DRY_STREAK,
    DEFAULT_NOTIFY_ON_RAIN,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_NOTIFY_SERVICES,
    DEFAULT_NOTIFY_TITLE,
    DEFAULT_RAIN_THRESHOLD_MM,
    DOMAIN,
)


def _format_notify_label(service_name: str) -> str:
    """Return a readable label for a notify service."""
    service = service_name.replace("notify.", "", 1)
    return service.replace("mobile_app_", "").replace("_", " ").title()


def _normalize_notify_services(value: Any) -> list[str]:
    """Return a normalized list of notify service ids."""
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return list(DEFAULT_NOTIFY_SERVICES)


def _notify_service_options(
    hass,
    selected_services: list[str],
) -> list[dict[str, str]]:
    """Return available notify services for the options UI."""
    services = {"notify.notify", *selected_services}
    for service in hass.services.async_services().get("notify", {}):
        services.add(f"notify.{service}")

    return [
        {"value": service, "label": _format_notify_label(service)}
        for service in sorted(
            services,
            key=lambda item: (
                not item.startswith("notify.mobile_app_"),
                item != "notify.notify",
                item,
            ),
        )
    ]


def _number_selector(
    minimum: float,
    maximum: float,
    step: float,
    unit: str,
) -> selector.NumberSelector:
    """Return a boxed number selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=minimum,
            max=maximum,
            step=step,
            mode=selector.NumberSelectorMode.BOX,
            unit_of_measurement=unit,
        )
    )


def _entry_schema(defaults: dict[str, Any], notify_options) -> vol.Schema:
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
            ): _number_selector(0, 5, 0.1, "mm"),
            vol.Optional(
                CONF_DRY_DAY_THRESHOLD_MM,
                default=defaults[CONF_DRY_DAY_THRESHOLD_MM],
            ): _number_selector(0, 5, 0.1, "mm"),
            vol.Optional(
                CONF_NOTIFY_ON_RAIN,
                default=defaults[CONF_NOTIFY_ON_RAIN],
            ): bool,
            vol.Optional(
                CONF_NOTIFY_SERVICES,
                default=defaults[CONF_NOTIFY_SERVICES],
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=notify_options,
                    multiple=True,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(
                CONF_NOTIFY_TITLE,
                default=defaults[CONF_NOTIFY_TITLE],
            ): selector.TextSelector(),
            vol.Optional(
                CONF_NOTIFY_MESSAGE,
                default=defaults[CONF_NOTIFY_MESSAGE],
            ): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True),
            ),
            vol.Optional(
                CONF_NOTIFY_COOLDOWN_MINUTES,
                default=defaults[CONF_NOTIFY_COOLDOWN_MINUTES],
            ): _number_selector(0, 1440, 5, "min"),
            vol.Optional(
                CONF_NOTIFY_ON_DRY_STREAK,
                default=defaults[CONF_NOTIFY_ON_DRY_STREAK],
            ): bool,
            vol.Optional(
                CONF_DRY_STREAK_THRESHOLD_DAYS,
                default=defaults[CONF_DRY_STREAK_THRESHOLD_DAYS],
            ): _number_selector(1, 60, 1, "days"),
            vol.Optional(
                CONF_DRY_NOTIFY_TITLE,
                default=defaults[CONF_DRY_NOTIFY_TITLE],
            ): selector.TextSelector(),
            vol.Optional(
                CONF_DRY_NOTIFY_MESSAGE,
                default=defaults[CONF_DRY_NOTIFY_MESSAGE],
            ): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True),
            ),
            vol.Optional(
                CONF_DRY_NOTIFY_COOLDOWN_MINUTES,
                default=defaults[CONF_DRY_NOTIFY_COOLDOWN_MINUTES],
            ): _number_selector(0, 10080, 60, "min"),
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
            CONF_DRY_DAY_THRESHOLD_MM: DEFAULT_DRY_DAY_THRESHOLD_MM,
            CONF_NOTIFY_ON_RAIN: DEFAULT_NOTIFY_ON_RAIN,
            CONF_NOTIFY_SERVICES: DEFAULT_NOTIFY_SERVICES,
            CONF_NOTIFY_TITLE: DEFAULT_NOTIFY_TITLE,
            CONF_NOTIFY_MESSAGE: DEFAULT_NOTIFY_MESSAGE,
            CONF_NOTIFY_COOLDOWN_MINUTES: DEFAULT_NOTIFY_COOLDOWN_MINUTES,
            CONF_NOTIFY_ON_DRY_STREAK: DEFAULT_NOTIFY_ON_DRY_STREAK,
            CONF_DRY_STREAK_THRESHOLD_DAYS: DEFAULT_DRY_STREAK_THRESHOLD_DAYS,
            CONF_DRY_NOTIFY_TITLE: DEFAULT_DRY_NOTIFY_TITLE,
            CONF_DRY_NOTIFY_MESSAGE: DEFAULT_DRY_NOTIFY_MESSAGE,
            CONF_DRY_NOTIFY_COOLDOWN_MINUTES: DEFAULT_DRY_NOTIFY_COOLDOWN_MINUTES,
        }
        return self.async_show_form(
            step_id="user",
            data_schema=_entry_schema(
                defaults,
                _notify_service_options(self.hass, defaults[CONF_NOTIFY_SERVICES]),
            ),
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
        merged = {**data, **options}
        notify_services = _normalize_notify_services(
            merged.get(
                CONF_NOTIFY_SERVICES,
                merged.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
            )
        )
        defaults = {
            CONF_NAME: merged.get(CONF_NAME, DEFAULT_NAME),
            CONF_LATITUDE: merged.get(CONF_LATITUDE, DEFAULT_LATITUDE),
            CONF_LONGITUDE: merged.get(CONF_LONGITUDE, DEFAULT_LONGITUDE),
            CONF_RAIN_THRESHOLD_MM: merged.get(
                CONF_RAIN_THRESHOLD_MM,
                DEFAULT_RAIN_THRESHOLD_MM,
            ),
            CONF_DRY_DAY_THRESHOLD_MM: merged.get(
                CONF_DRY_DAY_THRESHOLD_MM,
                DEFAULT_DRY_DAY_THRESHOLD_MM,
            ),
            CONF_NOTIFY_ON_RAIN: merged.get(
                CONF_NOTIFY_ON_RAIN,
                DEFAULT_NOTIFY_ON_RAIN,
            ),
            CONF_NOTIFY_SERVICES: notify_services,
            CONF_NOTIFY_TITLE: merged.get(CONF_NOTIFY_TITLE, DEFAULT_NOTIFY_TITLE),
            CONF_NOTIFY_MESSAGE: merged.get(CONF_NOTIFY_MESSAGE, DEFAULT_NOTIFY_MESSAGE),
            CONF_NOTIFY_COOLDOWN_MINUTES: merged.get(
                CONF_NOTIFY_COOLDOWN_MINUTES,
                DEFAULT_NOTIFY_COOLDOWN_MINUTES,
            ),
            CONF_NOTIFY_ON_DRY_STREAK: merged.get(
                CONF_NOTIFY_ON_DRY_STREAK,
                DEFAULT_NOTIFY_ON_DRY_STREAK,
            ),
            CONF_DRY_STREAK_THRESHOLD_DAYS: merged.get(
                CONF_DRY_STREAK_THRESHOLD_DAYS,
                DEFAULT_DRY_STREAK_THRESHOLD_DAYS,
            ),
            CONF_DRY_NOTIFY_TITLE: merged.get(
                CONF_DRY_NOTIFY_TITLE,
                DEFAULT_DRY_NOTIFY_TITLE,
            ),
            CONF_DRY_NOTIFY_MESSAGE: merged.get(
                CONF_DRY_NOTIFY_MESSAGE,
                DEFAULT_DRY_NOTIFY_MESSAGE,
            ),
            CONF_DRY_NOTIFY_COOLDOWN_MINUTES: merged.get(
                CONF_DRY_NOTIFY_COOLDOWN_MINUTES,
                DEFAULT_DRY_NOTIFY_COOLDOWN_MINUTES,
            ),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=_entry_schema(
                defaults,
                _notify_service_options(self.hass, notify_services),
            ),
        )
