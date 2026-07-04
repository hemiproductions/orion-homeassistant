"""Sensors backed by a single Orion /api/machine/summary poll."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OrionCoordinator


@dataclass(frozen=True, kw_only=True)
class OrionSensorDescription(SensorEntityDescription):
    """Describes how to read one sensor's state + attributes from the summary payload."""

    value_fn: Callable[[dict[str, Any]], Any]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[OrionSensorDescription, ...] = (
    OrionSensorDescription(
        key="up_next",
        name="Up next",
        icon="mdi:television-play",
        value_fn=lambda data: (data.get("next") or {}).get("show"),
        attrs_fn=lambda data: {"up_next": data.get("upNext", [])},
    ),
    OrionSensorDescription(
        key="airing_today",
        name="Airing today",
        icon="mdi:calendar-today",
        native_unit_of_measurement="items",
        value_fn=lambda data: data.get("counts", {}).get("airingToday", 0),
        attrs_fn=lambda data: {"today": data.get("today", [])},
    ),
    OrionSensorDescription(
        key="airing_week",
        name="Airing this week",
        icon="mdi:calendar-week",
        native_unit_of_measurement="items",
        value_fn=lambda data: data.get("counts", {}).get("airingWeek", 0),
        attrs_fn=lambda data: {"week": data.get("week", [])},
    ),
    OrionSensorDescription(
        key="unwatched_episodes",
        name="Unwatched episodes",
        icon="mdi:eye-off",
        native_unit_of_measurement="episodes",
        value_fn=lambda data: data.get("counts", {}).get("unwatchedEpisodes", 0),
    ),
    OrionSensorDescription(
        key="releasing_soon",
        name="Releasing soon",
        icon="mdi:new-box",
        native_unit_of_measurement="items",
        value_fn=lambda data: len(data.get("releasing", [])),
        attrs_fn=lambda data: {"releasing": data.get("releasing", [])},
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: OrionCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(OrionSensor(coordinator, entry, description) for description in SENSOR_DESCRIPTIONS)


class OrionSensor(CoordinatorEntity[OrionCoordinator], SensorEntity):
    """A single Orion summary field, refreshed from the shared coordinator."""

    entity_description: OrionSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: OrionCoordinator, entry: ConfigEntry, description: OrionSensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Orion",
            "manufacturer": "Orion",
        }

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
