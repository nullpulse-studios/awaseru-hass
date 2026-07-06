"""Weather entity for Bandabou Rain."""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import (
    BandabouRainDataUpdateCoordinator,
    _as_float,
    _as_timestamp,
)

PRECIPITATION_UNIT = "mm"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Bandabou Rain weather entity."""
    coordinator: BandabouRainDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([BandabouRainWeather(coordinator, entry)])


def _condition_from_code(code: Any, precipitation: float = 0.0) -> str:
    """Map Open-Meteo WMO weather codes to Home Assistant conditions."""
    code_int = int(_as_float(code, -1))

    if code_int in (95, 96, 99):
        return "lightning-rainy" if precipitation > 0 else "lightning"
    if code_int in (65, 82):
        return "pouring"
    if code_int in (51, 53, 55, 56, 57, 61, 63, 66, 67, 80, 81):
        return "rainy"
    if code_int in (45, 48):
        return "fog"
    if code_int == 0:
        return "sunny"
    if code_int in (1, 2):
        return "partlycloudy"
    if code_int == 3:
        return "cloudy"
    return "exceptional"


def _utc_datetime(value: Any) -> str:
    """Return a UTC RFC 3339 datetime string for Home Assistant forecasts."""
    from datetime import UTC, datetime

    return datetime.fromtimestamp(_as_timestamp(value), tz=UTC).isoformat()


class BandabouRainWeather(
    CoordinatorEntity[BandabouRainDataUpdateCoordinator],
    WeatherEntity,
):
    """Bandabou weather entity."""

    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )
    _attr_native_precipitation_unit = PRECIPITATION_UNIT
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(
        self,
        coordinator: BandabouRainDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._attr_name = "Bandabou Rain"
        self._attr_unique_id = f"{entry.entry_id}_weather"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Open-Meteo",
            model="Bandabou Rain Monitor",
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update state and notify forecast subscribers."""
        super()._handle_coordinator_update()
        self.hass.async_create_task(self.async_update_listeners())

    @property
    def condition(self) -> str:
        """Return the current weather condition."""
        return _condition_from_code(
            self.coordinator.current.get("weather_code"),
            self.coordinator.current_precipitation,
        )

    @property
    def native_temperature(self) -> float:
        """Return the current temperature."""
        return _as_float(self.coordinator.current.get("temperature_2m"))

    @property
    def native_apparent_temperature(self) -> float:
        """Return the apparent temperature."""
        return _as_float(self.coordinator.current.get("apparent_temperature"))

    @property
    def humidity(self) -> float:
        """Return current humidity."""
        return _as_float(self.coordinator.current.get("relative_humidity_2m"))

    @property
    def cloud_coverage(self) -> int:
        """Return current cloud coverage."""
        return round(_as_float(self.coordinator.current.get("cloud_cover")))

    @property
    def native_wind_speed(self) -> float:
        """Return current wind speed."""
        return _as_float(self.coordinator.current.get("wind_speed_10m"))

    @property
    def native_wind_gust_speed(self) -> float:
        """Return current wind gust speed."""
        return _as_float(self.coordinator.current.get("wind_gusts_10m"))

    @property
    def wind_bearing(self) -> float:
        """Return current wind bearing."""
        return _as_float(self.coordinator.current.get("wind_direction_10m"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return useful dashboard attributes."""
        return {
            "precipitation": self.coordinator.current_precipitation,
            "current_precipitation": self.coordinator.current_precipitation,
            "dry_days": self.coordinator.dry_days,
            "last_rain_date": self.coordinator.last_rain_date,
            "rain_threshold_mm": self.coordinator.threshold_mm,
            "dry_day_threshold_mm": self.coordinator.dry_day_threshold_mm,
            "dry_streak_threshold_days": self.coordinator.dry_streak_threshold_days,
            "rain_next_3_hours": self.coordinator.rain_next_3_hours,
            "max_rain_probability_next_3_hours": (
                self.coordinator.max_probability_next_3_hours
            ),
        }

    async def async_forecast_hourly(self) -> list[Forecast] | None:
        """Return hourly weather forecast data."""
        hourly = self.coordinator.hourly
        times = hourly.get("time", [])
        temperatures = hourly.get("temperature_2m", [])
        precipitation = hourly.get("precipitation", [])
        probability = hourly.get("precipitation_probability", [])
        weather_codes = hourly.get("weather_code", [])
        cloud_cover = hourly.get("cloud_cover", [])
        wind_speed = hourly.get("wind_speed_10m", [])
        wind_bearing = hourly.get("wind_direction_10m", [])
        wind_gusts = hourly.get("wind_gusts_10m", [])

        forecast: list[Forecast] = []
        for index, forecast_time in enumerate(times):
            precipitation_value = _as_float(
                precipitation[index] if index < len(precipitation) else None
            )
            forecast.append(
                {
                    "datetime": _utc_datetime(forecast_time),
                    "condition": _condition_from_code(
                        weather_codes[index] if index < len(weather_codes) else None,
                        precipitation_value,
                    ),
                    "native_temperature": _as_float(
                        temperatures[index] if index < len(temperatures) else None
                    ),
                    "native_precipitation": precipitation_value,
                    "precipitation_probability": round(
                        _as_float(probability[index] if index < len(probability) else None)
                    ),
                    "cloud_coverage": round(
                        _as_float(cloud_cover[index] if index < len(cloud_cover) else None)
                    ),
                    "native_wind_speed": _as_float(
                        wind_speed[index] if index < len(wind_speed) else None
                    ),
                    "native_wind_gust_speed": _as_float(
                        wind_gusts[index] if index < len(wind_gusts) else None
                    ),
                    "wind_bearing": _as_float(
                        wind_bearing[index] if index < len(wind_bearing) else None
                    ),
                }
            )

        return forecast

    async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return daily weather forecast data."""
        daily = self.coordinator.daily
        times = daily.get("time", [])
        precipitation = daily.get("precipitation_sum", [])
        probability = daily.get("precipitation_probability_max", [])
        weather_codes = daily.get("weather_code", [])
        temp_highs = daily.get("temperature_2m_max", [])
        temp_lows = daily.get("temperature_2m_min", [])

        forecast: list[Forecast] = []
        for index, forecast_time in enumerate(times):
            timestamp = _as_timestamp(forecast_time)
            if timestamp == 0 or timestamp < _as_timestamp(self.coordinator.today_date):
                continue

            precipitation_value = _as_float(
                precipitation[index] if index < len(precipitation) else None
            )
            forecast.append(
                {
                    "datetime": _utc_datetime(forecast_time),
                    "condition": _condition_from_code(
                        weather_codes[index] if index < len(weather_codes) else None,
                        precipitation_value,
                    ),
                    "native_temperature": _as_float(
                        temp_highs[index] if index < len(temp_highs) else None
                    ),
                    "native_templow": _as_float(
                        temp_lows[index] if index < len(temp_lows) else None
                    ),
                    "native_precipitation": precipitation_value,
                    "precipitation_probability": round(
                        _as_float(probability[index] if index < len(probability) else None)
                    ),
                }
            )

        return forecast[:7]
