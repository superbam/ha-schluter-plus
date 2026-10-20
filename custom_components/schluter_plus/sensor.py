"""Heating load and diagnostics the thermostat reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SchluterEntity


@dataclass(frozen=True, kw_only=True)
class SchluterSensorDescription(SensorEntityDescription):
    field: str


SENSORS = (
    SchluterSensorDescription(key="load_measured", field="LoadMeasuredWatt", translation_key="load_measured",
        device_class=SensorDeviceClass.POWER, native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT),
    SchluterSensorDescription(key="load_set", field="LoadManuallySetWatt", translation_key="load_set",
        device_class=SensorDeviceClass.POWER, native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC),
    SchluterSensorDescription(key="error_code", field="ErrorCode", translation_key="error_code",
        entity_category=EntityCategory.DIAGNOSTIC),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SchluterSensor(coordinator, serial, d) for serial in coordinator.data for d in SENSORS)


class SchluterSensor(SchluterEntity, SensorEntity):
    entity_description: SchluterSensorDescription

    def __init__(self, coordinator, serial, description: SchluterSensorDescription) -> None:
        super().__init__(coordinator, serial, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self._data.get(self.entity_description.field)
