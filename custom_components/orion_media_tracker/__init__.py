"""The Orion integration: media-tracker sensors, sync button, and write-back services."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OrionApiError, OrionClient
from .const import (
    ATTR_ARCHIVED,
    ATTR_FOLLOWED,
    ATTR_ITEM_ID,
    ATTR_KIND,
    ATTR_WATCHED,
    CONF_SCAN_INTERVAL,
    CONF_TOKEN,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    SERVICE_MARK_WATCHED,
    SERVICE_SET_FOLLOWED,
)
from .coordinator import OrionCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]

MARK_WATCHED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_KIND): vol.In(["episode", "movie", "game"]),
        vol.Required(ATTR_ITEM_ID): cv.positive_int,
        vol.Required(ATTR_WATCHED): cv.boolean,
    }
)

SET_FOLLOWED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_KIND): vol.In(["show", "movie", "game"]),
        vol.Required(ATTR_ITEM_ID): cv.positive_int,
        vol.Optional(ATTR_FOLLOWED): cv.boolean,
        vol.Optional(ATTR_ARCHIVED): cv.boolean,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = OrionClient(session, entry.data[CONF_URL], entry.data[CONF_TOKEN])

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
    coordinator = OrionCoordinator(hass, client, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    async def _mark_watched(call: ServiceCall) -> None:
        try:
            await client.mark_watched(call.data[ATTR_KIND], call.data[ATTR_ITEM_ID], call.data[ATTR_WATCHED])
        except OrionApiError as err:
            raise HomeAssistantError(f"orion.mark_watched failed: {err}") from err
        await coordinator.async_request_refresh()

    async def _set_followed(call: ServiceCall) -> None:
        try:
            await client.set_followed(
                call.data[ATTR_KIND],
                call.data[ATTR_ITEM_ID],
                followed=call.data.get(ATTR_FOLLOWED),
                archived=call.data.get(ATTR_ARCHIVED),
            )
        except OrionApiError as err:
            raise HomeAssistantError(f"orion.set_followed failed: {err}") from err
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_MARK_WATCHED, _mark_watched, schema=MARK_WATCHED_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_FOLLOWED, _set_followed, schema=SET_FOLLOWED_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_MARK_WATCHED)
            hass.services.async_remove(DOMAIN, SERVICE_SET_FOLLOWED)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
