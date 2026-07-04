"""DataUpdateCoordinator polling Orion's consolidated summary feed."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OrionApiError, OrionClient

_LOGGER = logging.getLogger(__name__)


class OrionCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetches /api/machine/summary once per interval; every entity reads from it."""

    def __init__(self, hass: HomeAssistant, client: OrionClient, scan_interval_minutes: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="orion_media_tracker",
            update_interval=timedelta(minutes=scan_interval_minutes),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.get_summary()
        except OrionApiError as err:
            raise UpdateFailed(str(err)) from err
