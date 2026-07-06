"""Button entities for Bandabou Rain."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BandabouRainDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bandabou Rain buttons."""
    coordinator: BandabouRainDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            BandabouRainTestButton(
                coordinator,
                entry,
                "test_rain_notification",
                "Bandabou Rain Test Rain Notification",
                "mdi:bell-ring",
                coordinator.async_send_test_rain_notification,
            ),
            BandabouRainTestButton(
                coordinator,
                entry,
                "test_dry_streak_notification",
                "Bandabou Rain Test Dry Streak Notification",
                "mdi:white-balance-sunny",
                coordinator.async_send_test_dry_streak_notification,
            ),
        ]
    )


class BandabouRainTestButton(
    CoordinatorEntity[BandabouRainDataUpdateCoordinator],
    ButtonEntity,
):
    """Button that sends a configured test notification."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: BandabouRainDataUpdateCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
        action: Callable[[], Awaitable[bool]],
    ) -> None:
        """Initialize the test notification button."""
        super().__init__(coordinator)
        self._action = action
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Open-Meteo",
            model="Bandabou Rain Monitor",
        )

    async def async_press(self) -> None:
        """Send the configured test notification."""
        if not await self._action():
            raise HomeAssistantError(
                "No notification was sent. Check the Bandabou Rain notification services."
            )
