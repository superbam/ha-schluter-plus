"""Climate entity: current/target temperature, heating action, schedule/manual presets and off.

Drop-in replacement for the built-in Schluter integration's climate entity, with what that one lacks:
 - hvac mode "heat" follows the programmed schedule; "off" parks the floor at the minimum temperature (frost protection only);
 - presets "schedule" and "manual";
 - setting a temperature switches to manual at that temperature (as the built-in does).
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import helpers
from .const import DOMAIN
from .entity import SchluterEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SchluterClimate(coordinator, serial) for serial in coordinator.data)


class SchluterClimate(SchluterEntity, ClimateEntity):
    _attr_name = None  # the device name (the room) is the entity name
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_preset_modes = [helpers.PRESET_SCHEDULE, helpers.PRESET_MANUAL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    def __init__(self, coordinator, serial) -> None:
        super().__init__(coordinator, serial, "climate")

    @property
    def available(self) -> bool:
        return super().available and bool(self._data.get("Online", True))

    @property
    def current_temperature(self) -> float | None:
        return helpers.celsius(self._data.get("Temperature"))

    @property
    def target_temperature(self) -> float | None:
        return helpers.celsius(self._data.get("SetPointTemp"))

    @property
    def min_temp(self) -> float:
        return helpers.min_temp(self._data)

    @property
    def max_temp(self) -> float:
        return helpers.max_temp(self._data)

    @property
    def hvac_mode(self) -> HVACMode:
        return HVACMode.OFF if helpers.is_off(self._data) else HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        if helpers.is_off(self._data):
            return HVACAction.OFF
        return HVACAction.HEATING if self._data.get("Heating") else HVACAction.IDLE

    @property
    def preset_mode(self) -> str | None:
        return helpers.preset(self._data)

    async def _apply(self, payload: dict[str, Any]) -> None:
        await self.coordinator.async_command(self._serial, payload)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (value := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._apply(helpers.manual_payload(self._serial, value))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.OFF:
            await self._apply(helpers.off_payload(self._serial, self._data))
        else:
            await self._apply(helpers.heat_payload(self._serial))

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        if preset_mode == helpers.PRESET_SCHEDULE:
            await self._apply(helpers.heat_payload(self._serial))
        else:
            await self._apply({"SerialNumber": self._serial, "RegulationMode": helpers.MODE_MANUAL})
