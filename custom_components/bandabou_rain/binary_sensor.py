"""Binary sensors for Bandabou Rain."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BandabouRainDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bandabou Rain binary sensor."""
    coordinator: BandabouRainDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BandabouRainingBinarySensor(coordinator, entry)])


class BandabouRainingBinarySensor(
    CoordinatorEntity[BandabouRainDataUpdateCoordinator],
    BinarySensorEntity,
):
    """Whether it is currently raining in Bandabou."""

    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_icon = "mdi:weather-pouring"

    def __init__(
        self,
        coordinator: BandabouRainDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_name = "Bandabou Rain Raining"
        self._attr_unique_id = f"{entry.entry_id}_raining"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Open-Meteo",
            model="Bandabou Rain Monitor",
        )

    @property
    def is_on(self) -> bool:
        """Return whether it is raining."""
        return self.coordinator.is_raining

    @property
    def extra_state_attributes(self) -> dict[str, float]:
        """Return useful rain detection values."""
        return {
            "rain_threshold_mm": self.coordinator.threshold_mm,
            "dry_day_threshold_mm": self.coordinator.dry_day_threshold_mm,
            "current_precipitation_mm": self.coordinator.current_precipitation,
            "current_rain_mm": self.coordinator.current_rain,
            "current_showers_mm": self.coordinator.current_showers,
        }
