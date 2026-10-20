"""Polls the Schluter cloud once for all thermostats."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import helpers
from .api import InvalidAuth, SchluterClient, SchluterError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class SchluterCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    def __init__(self, hass: HomeAssistant, client: SchluterClient) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.client = client

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            return await self.client.async_get_thermostats()
        except InvalidAuth as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except SchluterError as err:
            raise UpdateFailed(str(err)) from err

    async def async_command(self, serial: str, payload: dict[str, Any]) -> None:
        """Send a change, show it immediately, then re-read once the cloud has applied it.

        The Schluter cloud takes a few seconds to apply a change, so an immediate re-read returns the old state.
        """
        await self.client.async_update_thermostat(serial, payload)
        if serial in self.data:
            self.async_set_updated_data({**self.data, serial: helpers.apply_optimistic(self.data[serial], payload)})
        self.hass.async_create_background_task(self._refresh_later(), name="schluter_plus refresh after command")

    async def _refresh_later(self) -> None:
        for delay in (6, 10):
            await asyncio.sleep(delay)
            await self.async_refresh()
