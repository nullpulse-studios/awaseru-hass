"""Client for the Open-Meteo forecast API."""

from __future__ import annotations

import asyncio
from typing import Any

from aiohttp import ClientError, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


class OpenMeteoError(Exception):
    """Raised when Open-Meteo cannot return usable weather data."""


class OpenMeteoClient:
    """Small async Open-Meteo API client."""

    def __init__(self, hass: HomeAssistant, latitude: float, longitude: float) -> None:
        """Initialize the API client."""
        self._session = async_get_clientsession(hass)
        self._latitude = latitude
        self._longitude = longitude

    async def async_get_forecast(self) -> dict[str, Any]:
        """Fetch the current rain state, forecast, and recent daily rain history."""
        params = {
            "latitude": self._latitude,
            "longitude": self._longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,apparent_temperature,"
                "precipitation,rain,showers,weather_code,cloud_cover,"
                "wind_speed_10m,wind_direction_10m,wind_gusts_10m"
            ),
            "hourly": (
                "temperature_2m,precipitation,precipitation_probability,"
                "rain,showers,weather_code,cloud_cover,wind_speed_10m,"
                "wind_direction_10m,wind_gusts_10m"
            ),
            "daily": (
                "weather_code,temperature_2m_max,temperature_2m_min,"
                "precipitation_sum,rain_sum,showers_sum,"
                "precipitation_probability_max"
            ),
            "forecast_hours": 24,
            "forecast_days": 7,
            "past_days": 31,
            "timezone": "America/Curacao",
            "timeformat": "iso8601",
        }

        try:
            async with self._session.get(
                OPEN_METEO_FORECAST_URL,
                params=params,
                timeout=ClientTimeout(total=20),
            ) as response:
                response.raise_for_status()
                data: dict[str, Any] = await response.json()
        except (asyncio.TimeoutError, ClientError) as err:
            raise OpenMeteoError(f"Open-Meteo request failed: {err}") from err

        if "current" not in data or "hourly" not in data or "daily" not in data:
            raise OpenMeteoError("Open-Meteo response did not include forecast data")

        return data
