"""A single button entity that triggers a manual Orion catalog refresh."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OrionCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: OrionCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OrionSyncButton(coordinator, entry)])


class OrionSyncButton(CoordinatorEntity[OrionCoordinator], ButtonEntity):
    """POSTs /api/machine/sync, then refreshes the coordinator's data."""

    _attr_has_entity_name = True
    _attr_name = "Sync now"
    _attr_icon = "mdi:sync"

    def __init__(self, coordinator: OrionCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_sync"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Orion",
            "manufacturer": "Orion",
        }

    async def async_press(self) -> None:
        await self.coordinator.client.trigger_sync()
        await self.coordinator.async_request_refresh()
