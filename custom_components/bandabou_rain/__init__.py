"""Bandabou Rain custom integration."""

from __future__ import annotations

from pathlib import Path

try:
    from homeassistant.components.http import StaticPathConfig
except ImportError:  # pragma: no cover - compatibility with older HA versions
    StaticPathConfig = None

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import BandabouRainDataUpdateCoordinator

STATIC_PATH = f"/{DOMAIN}"
STATIC_REGISTERED = f"{DOMAIN}_static_registered"
WWW_PATH = Path(__file__).parent / "www"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bandabou Rain from a config entry."""
    await _async_register_static_path(hass)

    coordinator = BandabouRainDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_static_path(hass: HomeAssistant) -> None:
    """Serve bundled dashboard card assets."""
    if hass.data.get(STATIC_REGISTERED):
        return

    if StaticPathConfig is not None and hasattr(
        hass.http,
        "async_register_static_paths",
    ):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_PATH, str(WWW_PATH), True)]
        )
    else:
        hass.http.register_static_path(STATIC_PATH, str(WWW_PATH), True)

    hass.data[STATIC_REGISTERED] = True
