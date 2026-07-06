"""Sensors for Bandabou Rain."""

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
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BandabouRainDataUpdateCoordinator

PRECIPITATION_UNIT = "mm"


@dataclass(frozen=True, kw_only=True)
class BandabouRainSensorEntityDescription(SensorEntityDescription):
    """Sensor entity description with a value callback."""

    value_fn: Callable[[BandabouRainDataUpdateCoordinator], float]
    attrs_fn: Callable[[BandabouRainDataUpdateCoordinator], dict[str, Any]] | None = None


SENSORS: tuple[BandabouRainSensorEntityDescription, ...] = (
    BandabouRainSensorEntityDescription(
        key="current_precipitation",
        name="Bandabou Rain Current Precipitation",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PRECIPITATION_UNIT,
        icon="mdi:weather-rainy",
        value_fn=lambda coordinator: coordinator.current_precipitation,
        attrs_fn=lambda coordinator: {
            "forecast": coordinator.forecast,
            "current_rain_mm": coordinator.current_rain,
            "current_showers_mm": coordinator.current_showers,
            "threshold_mm": coordinator.threshold_mm,
        },
    ),
    BandabouRainSensorEntityDescription(
        key="rain_next_3_hours",
        name="Bandabou Rain Rain Next 3 Hours",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PRECIPITATION_UNIT,
        icon="mdi:weather-pouring",
        value_fn=lambda coordinator: coordinator.rain_next_3_hours,
    ),
    BandabouRainSensorEntityDescription(
        key="max_rain_probability_next_3_hours",
        name="Bandabou Rain Max Rain Probability Next 3 Hours",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:water-percent",
        value_fn=lambda coordinator: coordinator.max_probability_next_3_hours,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bandabou Rain sensors."""
    coordinator: BandabouRainDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        BandabouRainSensor(coordinator, entry, description) for description in SENSORS
    )


class BandabouRainSensor(
    CoordinatorEntity[BandabouRainDataUpdateCoordinator],
    SensorEntity,
):
    """Bandabou Rain sensor."""

    entity_description: BandabouRainSensorEntityDescription

    def __init__(
        self,
        coordinator: BandabouRainDataUpdateCoordinator,
        entry: ConfigEntry,
        description: BandabouRainSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Open-Meteo",
            model="Bandabou Rain Monitor",
        )

    @property
    def native_value(self) -> float:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator)
