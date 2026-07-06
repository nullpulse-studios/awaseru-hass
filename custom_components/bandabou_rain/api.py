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
        """Fetch the current and 24-hour rain forecast."""
        params = {
            "latitude": self._latitude,
            "longitude": self._longitude,
            "current": "precipitation,rain,showers,weather_code",
            "hourly": "precipitation,precipitation_probability,rain,showers",
            "forecast_hours": 24,
            "timezone": "UTC",
            "timeformat": "unixtime",
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

        if "current" not in data or "hourly" not in data:
            raise OpenMeteoError("Open-Meteo response did not include forecast data")

        return data
