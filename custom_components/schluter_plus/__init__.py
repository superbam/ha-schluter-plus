"""Schluter DITRA-HEAT Plus: mode, load and heating entities the built-in integration lacks."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

import logging

from .api import SchluterClient
from .const import CONF_LOCAL_MODE, DOMAIN, GATEWAY_PORT, LOCAL_OFF, LOCAL_RELAY
from .coordinator import SchluterCoordinator
from .local_cert import async_ensure_cert
from .local_gateway import LocalGateway

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE, Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = SchluterClient(async_get_clientsession(hass), entry.data[CONF_EMAIL], entry.data[CONF_PASSWORD])
    coordinator = SchluterCoordinator(hass, client)
    mode = entry.options.get(CONF_LOCAL_MODE, LOCAL_OFF)
    if mode != LOCAL_OFF:
        # Start listening first so a thermostat that is already redirected here can connect during the first cloud read.
        certfile, keyfile = await async_ensure_cert(hass)
        gateway = LocalGateway(certfile, keyfile, relay=mode == LOCAL_RELAY, on_state=coordinator.handle_local_state)
        try:
            await gateway.start(hass)
            coordinator.gateway = gateway
        except OSError as err:  # most likely port 9533 is taken (for example by another Schluter integration)
            _LOGGER.error("Can't start the local gateway on port %s (%s); continuing with the cloud only", GATEWAY_PORT, err)
    try:
        await coordinator.async_config_entry_first_refresh()
    except BaseException:
        if coordinator.gateway:
            await coordinator.gateway.stop()
        raise
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_options_updated))
    return True


async def _options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        if coordinator.gateway:
            await coordinator.gateway.stop()
    return unloaded
