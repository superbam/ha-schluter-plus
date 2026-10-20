"""Regulation mode: lets automations return a thermostat to its schedule."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MODE_NAMES
from .entity import SchluterEntity

NAME_TO_MODE = {v: k for k, v in MODE_NAMES.items()}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SchluterModeSelect(coordinator, serial) for serial in coordinator.data)


class SchluterModeSelect(SchluterEntity, SelectEntity):
    _attr_translation_key = "mode"
    _attr_options = list(NAME_TO_MODE)

    def __init__(self, coordinator, serial) -> None:
        super().__init__(coordinator, serial, "mode")

    @property
    def current_option(self) -> str | None:
        return MODE_NAMES.get(self._data.get("RegulationMode"))

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.client.async_set_mode(self._serial, NAME_TO_MODE[option])
        await self.coordinator.async_request_refresh()
