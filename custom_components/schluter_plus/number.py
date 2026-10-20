"""Manual temperature: the setpoint used in manual mode (e.g. a low 'away' temperature)."""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SchluterEntity


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SchluterManualTemperature(coordinator, serial) for serial in coordinator.data)


class SchluterManualTemperature(SchluterEntity, NumberEntity):
    _attr_translation_key = "manual_temperature"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS  # the API reports hundredths of a degree C
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, serial) -> None:
        super().__init__(coordinator, serial, "manual_temperature")

    @property
    def native_value(self) -> float | None:
        v = self._data.get("ManualTemperature")
        return None if v is None else v / 100

    @property
    def native_min_value(self) -> float:
        return self._data.get("MinTemp", 500) / 100

    @property
    def native_max_value(self) -> float:
        return self._data.get("MaxTemp", 4000) / 100

    async def async_set_native_value(self, value: float) -> None:
        # Only changes the stored manual temperature; select "manual" in Mode to apply it.
        await self.coordinator.client.async_update_thermostat(
            self._serial, {"SerialNumber": self._serial, "ManualTemperature": int(round(value * 100))}
        )
        await self.coordinator.async_request_refresh()
