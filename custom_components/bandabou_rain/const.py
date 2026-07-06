"""Constants for Bandabou Rain."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "bandabou_rain"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.WEATHER]

DEFAULT_NAME = "Bandabou Rain"
DEFAULT_LATITUDE = 12.267
DEFAULT_LONGITUDE = -69.100
DEFAULT_RAIN_THRESHOLD_MM = 0.1
DEFAULT_NOTIFY_ON_RAIN = True
DEFAULT_NOTIFY_SERVICE = "notify.notify"
DEFAULT_UPDATE_INTERVAL_SECONDS = 300

CONF_RAIN_THRESHOLD_MM = "rain_threshold_mm"
CONF_NOTIFY_ON_RAIN = "notify_on_rain"
CONF_NOTIFY_SERVICE = "notify_service"
