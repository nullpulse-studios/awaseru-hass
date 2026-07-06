"""Constants for Bandabou Rain."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "bandabou_rain"
PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.WEATHER]

DEFAULT_NAME = "Bandabou Rain"
DEFAULT_LATITUDE = 12.267
DEFAULT_LONGITUDE = -69.100
DEFAULT_RAIN_THRESHOLD_MM = 0.1
DEFAULT_DRY_DAY_THRESHOLD_MM = 0.1
DEFAULT_NOTIFY_ON_RAIN = True
DEFAULT_NOTIFY_SERVICE = "notify.notify"
DEFAULT_NOTIFY_SERVICES = [DEFAULT_NOTIFY_SERVICE]
DEFAULT_NOTIFY_TITLE = "Rain in Bandabou"
DEFAULT_NOTIFY_MESSAGE = (
    "It looks like rain has started in Bandabou. "
    "Current precipitation is {current_precipitation:.1f} mm. "
    "Next 3 hours: {rain_next_3_hours:.1f} mm, "
    "max probability {max_rain_probability_next_3_hours:.0f}%. "
    "Dry days before this: {dry_days}."
)
DEFAULT_NOTIFY_COOLDOWN_MINUTES = 120
DEFAULT_UPDATE_INTERVAL_SECONDS = 300

CONF_RAIN_THRESHOLD_MM = "rain_threshold_mm"
CONF_DRY_DAY_THRESHOLD_MM = "dry_day_threshold_mm"
CONF_NOTIFY_ON_RAIN = "notify_on_rain"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_SERVICES = "notify_services"
CONF_NOTIFY_TITLE = "notify_title"
CONF_NOTIFY_MESSAGE = "notify_message"
CONF_NOTIFY_COOLDOWN_MINUTES = "notify_cooldown_minutes"
