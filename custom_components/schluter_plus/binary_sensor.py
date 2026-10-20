"""Heating, online and vacation flags."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity, BinarySensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SchluterEntity


@dataclass(frozen=True, kw_only=True)
class SchluterBinaryDescription(BinarySensorEntityDescription):
    field: str


BINARY_SENSORS = (
    SchluterBinaryDescription(key="heating", field="Heating", translation_key="heating", device_class=BinarySensorDeviceClass.HEAT),
    SchluterBinaryDescription(key="online", field="Online", translation_key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY, entity_category=EntityCategory.DIAGNOSTIC),
    SchluterBinaryDescription(key="vacation", field="VacationEnabled", translation_key="vacation"),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(SchluterBinary(coordinator, serial, d) for serial in coordinator.data for d in BINARY_SENSORS)


class SchluterBinary(SchluterEntity, BinarySensorEntity):
    entity_description: SchluterBinaryDescription

    def __init__(self, coordinator, serial, description: SchluterBinaryDescription) -> None:
        super().__init__(coordinator, serial, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        v = self._data.get(self.entity_description.field)
        return None if v is None else bool(v)
