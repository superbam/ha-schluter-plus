"""Polls the Schluter cloud once for all thermostats."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import helpers
from .api import InvalidAuth, SchluterClient, SchluterError
from .const import DOMAIN, SCAN_INTERVAL
from .local_gateway import LocalGateway

_LOGGER = logging.getLogger(__name__)


class SchluterCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    def __init__(self, hass: HomeAssistant, client: SchluterClient) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.client = client
        self.gateway: LocalGateway | None = None  # set by __init__ when a local mode is on
        self._cloud: dict[str, dict[str, Any]] = {}  # the last thing the cloud told us
        self._local: dict[str, dict[str, Any]] = {}  # the last thing each thermostat told the gateway

    def _merged(self) -> dict[str, dict[str, Any]]:
        connected = self.gateway.connected_serials if self.gateway else set()
        return {serial: helpers.merge_local(rec, self._local.get(serial), serial in connected) for serial, rec in self._cloud.items()}

    @callback
    def handle_local_state(self, serial: str, fields: dict[str, Any]) -> None:
        """The gateway heard from a thermostat: show it now, without moving the cloud poll timer."""
        self._local.setdefault(serial, {}).update(fields)
        if serial in self._cloud:
            self.data = self._merged()  # not async_set_updated_data: that would restart the cloud poll timer
            self.async_update_listeners()

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        try:
            self._cloud = await self.client.async_get_thermostats()
            return self._merged()
        except InvalidAuth as err:
            if self._local_serving():
                _LOGGER.warning("Schluter cloud rejected the login (%s); serving the locally connected thermostats", err)
                return self._merged()
            raise ConfigEntryAuthFailed(str(err)) from err
        except SchluterError as err:
            if self._local_serving():
                _LOGGER.debug("Schluter cloud unavailable (%s); serving the locally connected thermostats", err)
                return self._merged()
            raise UpdateFailed(str(err)) from err

    def _local_serving(self) -> bool:
        """True when the cloud list we already have is usable and at least one thermostat is connected locally."""
        return bool(self._cloud and self.gateway and self.gateway.connected_serials)

    async def async_command(self, serial: str, payload: dict[str, Any]) -> None:
        """Send a change, show it immediately, then re-read once the cloud has applied it.

        The Schluter cloud takes a few seconds to apply a change, so an immediate re-read returns the old state.
        """
        local = helpers.local_command(payload, self.data.get(serial, {})) if self.gateway and serial in self.gateway.connected_serials else None
        if local is not None:
            await self.gateway.queue_set(serial, *local)  # straight to the thermostat; works with the cloud down
        else:
            await self.client.async_update_thermostat(serial, payload)
        if serial in self.data:
            self.async_set_updated_data({**self.data, serial: helpers.apply_optimistic(self.data[serial], payload)})
        self.hass.async_create_background_task(self._refresh_later(), name="schluter_plus refresh after command")

    async def _refresh_later(self) -> None:
        for delay in (6, 10):
            await asyncio.sleep(delay)
            await self.async_refresh()
