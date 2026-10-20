"""Shared base entity: one HA device per thermostat."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SchluterCoordinator


class SchluterEntity(CoordinatorEntity[SchluterCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: SchluterCoordinator, serial: str, key: str) -> None:
        super().__init__(coordinator)
        self._serial = serial
        self._attr_unique_id = f"{serial}_{key}"

    @property
    def _data(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._serial, {})

    @property
    def available(self) -> bool:
        return super().available and self._serial in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        d = self._data
        return DeviceInfo(
            identifiers={(DOMAIN, self._serial)},
            name=f"Schluter {d.get('Room', self._serial)}",
            manufacturer="Schluter",
            model="DITRA-HEAT-E-WiFi",
            sw_version=d.get("SWVersion"),
            serial_number=self._serial,
        )
