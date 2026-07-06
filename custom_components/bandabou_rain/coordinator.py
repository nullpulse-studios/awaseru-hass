"""Data coordinator for Bandabou Rain."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
import logging
from typing import Any
from zoneinfo import ZoneInfo

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OpenMeteoClient, OpenMeteoError
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
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)
LOCAL_TZ = ZoneInfo("America/Curacao")


def _as_float(value: Any, default: float = 0.0) -> float:
    """Convert a value to float without raising."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_timestamp(value: Any) -> float:
    """Convert an Open-Meteo timestamp to a Unix timestamp."""
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value)
    try:
        if len(text) == 10:
            parsed = datetime.combine(date.fromisoformat(text), time.min, LOCAL_TZ)
        else:
            parsed = datetime.fromisoformat(text)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=LOCAL_TZ)
    except ValueError:
        return 0.0

    return parsed.timestamp()


def _as_local_date(value: Any) -> date | None:
    """Convert an Open-Meteo date or timestamp to a Curacao local date."""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=UTC).astimezone(LOCAL_TZ).date()

    text = str(value)
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


class BandabouRainDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates Open-Meteo polling and rain notification state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self._client = OpenMeteoClient(hass, self.latitude, self.longitude)
        self._last_is_raining: bool | None = None

        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL_SECONDS),
        )

    @property
    def config(self) -> dict[str, Any]:
        """Return merged entry data and options."""
        return {**self.entry.data, **self.entry.options}

    @property
    def display_name(self) -> str:
        """Return the configured display name."""
        return str(self.config.get(CONF_NAME, DEFAULT_NAME))

    @property
    def latitude(self) -> float:
        """Return configured latitude."""
        return _as_float(self.config.get(CONF_LATITUDE), DEFAULT_LATITUDE)

    @property
    def longitude(self) -> float:
        """Return configured longitude."""
        return _as_float(self.config.get(CONF_LONGITUDE), DEFAULT_LONGITUDE)

    @property
    def threshold_mm(self) -> float:
        """Return configured rain threshold."""
        return _as_float(
            self.config.get(CONF_RAIN_THRESHOLD_MM),
            DEFAULT_RAIN_THRESHOLD_MM,
        )

    @property
    def notify_on_rain(self) -> bool:
        """Return whether rain notifications are enabled."""
        return bool(self.config.get(CONF_NOTIFY_ON_RAIN, DEFAULT_NOTIFY_ON_RAIN))

    @property
    def notify_service(self) -> str:
        """Return the configured notify service."""
        return str(self.config.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE))

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Open-Meteo."""
        try:
            data = await self._client.async_get_forecast()
        except OpenMeteoError as err:
            raise UpdateFailed(str(err)) from err

        await self._async_maybe_notify(data)
        return data

    @property
    def current(self) -> dict[str, Any]:
        """Return current weather data."""
        return (self.data or {}).get("current", {})

    @property
    def hourly(self) -> dict[str, list[Any]]:
        """Return hourly forecast data."""
        return (self.data or {}).get("hourly", {})

    @property
    def daily(self) -> dict[str, list[Any]]:
        """Return recent daily rain totals."""
        return (self.data or {}).get("daily", {})

    @property
    def today_date(self) -> date:
        """Return today's date in Curacao."""
        return datetime.now(LOCAL_TZ).date()

    @property
    def current_precipitation(self) -> float:
        """Return current precipitation in millimeters."""
        return _as_float(self.current.get("precipitation"))

    @property
    def current_rain(self) -> float:
        """Return current rain in millimeters."""
        return _as_float(self.current.get("rain"))

    @property
    def current_showers(self) -> float:
        """Return current showers in millimeters."""
        return _as_float(self.current.get("showers"))

    @property
    def is_raining(self) -> bool:
        """Return whether the current values meet the rain threshold."""
        return self._is_raining(self.data or {})

    @property
    def rain_next_3_hours(self) -> float:
        """Return total forecast precipitation for the next three hours."""
        values = self.hourly.get("precipitation", [])
        return round(sum(_as_float(value) for value in values[:3]), 2)

    @property
    def max_probability_next_3_hours(self) -> float:
        """Return max forecast precipitation probability for the next three hours."""
        values = self.hourly.get("precipitation_probability", [])
        probabilities = [_as_float(value) for value in values[:3]]
        return round(max(probabilities, default=0.0), 0)

    @property
    def dry_days(self) -> int:
        """Return the consecutive completed days without rain."""
        streak = 0
        for point in reversed(self.daily_history):
            if not point["is_dry"]:
                break
            streak += 1
        return streak

    @property
    def last_rain_date(self) -> str | None:
        """Return the most recent completed day with rain."""
        for point in reversed(self.daily_history):
            if not point["is_dry"]:
                return str(point["date"])
        return None

    @property
    def daily_history(self) -> list[dict[str, Any]]:
        """Return completed local-day rain history for dashboard cards."""
        daily = self.daily
        times = daily.get("time", [])
        precipitation = daily.get("precipitation_sum", [])
        rain = daily.get("rain_sum", [])
        showers = daily.get("showers_sum", [])
        today = self.today_date

        points: list[dict[str, Any]] = []
        for index, day_value in enumerate(times):
            local_day = _as_local_date(day_value)
            if local_day is None or local_day >= today:
                continue

            precipitation_sum = _as_float(
                precipitation[index] if index < len(precipitation) else None
            )
            points.append(
                {
                    "date": local_day.isoformat(),
                    "timestamp": _as_timestamp(day_value),
                    "precipitation_sum": precipitation_sum,
                    "rain_sum": _as_float(rain[index] if index < len(rain) else None),
                    "showers_sum": _as_float(
                        showers[index] if index < len(showers) else None
                    ),
                    "is_dry": precipitation_sum < self.threshold_mm,
                }
            )

        return points

    @property
    def forecast(self) -> list[dict[str, Any]]:
        """Return forecast points for dashboard cards."""
        hourly = self.hourly
        times = hourly.get("time", [])
        precipitation = hourly.get("precipitation", [])
        probability = hourly.get("precipitation_probability", [])
        rain = hourly.get("rain", [])
        showers = hourly.get("showers", [])

        points: list[dict[str, Any]] = []
        for index, timestamp in enumerate(times):
            timestamp_float = _as_timestamp(timestamp)
            points.append(
                {
                    "datetime": datetime.fromtimestamp(
                        timestamp_float,
                        tz=UTC,
                    ).isoformat(),
                    "timestamp": timestamp_float,
                    "precipitation": _as_float(
                        precipitation[index] if index < len(precipitation) else None
                    ),
                    "precipitation_probability": _as_float(
                        probability[index] if index < len(probability) else None
                    ),
                    "rain": _as_float(rain[index] if index < len(rain) else None),
                    "showers": _as_float(
                        showers[index] if index < len(showers) else None
                    ),
                }
            )
        return points

    def _is_raining(self, data: dict[str, Any]) -> bool:
        """Return whether the supplied data means it is raining."""
        current = data.get("current", {})
        threshold = self.threshold_mm
        return (
            _as_float(current.get("precipitation")) >= threshold
            or _as_float(current.get("rain")) >= threshold
            or _as_float(current.get("showers")) >= threshold
        )

    async def _async_maybe_notify(self, data: dict[str, Any]) -> None:
        """Send a Home Assistant notification when rain starts."""
        is_raining = self._is_raining(data)
        current = data.get("current", {})
        hourly = data.get("hourly", {})
        next_3_hours = round(
            sum(_as_float(value) for value in hourly.get("precipitation", [])[:3]),
            2,
        )
        probabilities = [
            _as_float(value)
            for value in hourly.get("precipitation_probability", [])[:3]
        ]
        max_probability = round(max(probabilities, default=0.0), 0)
        should_notify = (
            self.notify_on_rain
            and self._last_is_raining is False
            and is_raining
            and "." in self.notify_service
        )
        self._last_is_raining = is_raining

        if not should_notify:
            return

        domain, service = self.notify_service.split(".", 1)
        if not self.hass.services.has_service(domain, service):
            return

        await self.hass.services.async_call(
            domain,
            service,
            {
                "title": "Rain in Bandabou",
                "message": (
                    "It looks like rain has started in Bandabou. "
                    "Current precipitation is "
                    f"{_as_float(current.get('precipitation')):.1f} mm. "
                    f"Next 3 hours: {next_3_hours:.1f} mm, "
                    f"max probability {max_probability:.0f}%."
                ),
            },
            blocking=False,
        )
