"""Pure functions mapping the Schluter API record to Home Assistant climate concepts (testable without HA)."""
from __future__ import annotations

from typing import Any

MODE_SCHEDULE, MODE_COMFORT, MODE_MANUAL = 1, 2, 3
PRESET_SCHEDULE, PRESET_MANUAL = "schedule", "manual"
OFF_MARGIN_C = 0.6  # a manual setpoint within this of the minimum counts as "off"


def celsius(raw: Any) -> float | None:
    """The API reports hundredths of a degree Celsius."""
    return None if raw is None else raw / 100


def min_temp(d: dict[str, Any]) -> float:
    return celsius(d.get("MinTemp", 500))


def max_temp(d: dict[str, Any]) -> float:
    return celsius(d.get("MaxTemp", 4000))


def is_off(d: dict[str, Any]) -> bool:
    """Off = manual mode parked at (or next to) the minimum temperature: the floor won't heat, only frost protection remains."""
    sp = celsius(d.get("SetPointTemp"))
    return d.get("RegulationMode") == MODE_MANUAL and sp is not None and sp <= min_temp(d) + OFF_MARGIN_C


def preset(d: dict[str, Any]) -> str | None:
    mode = d.get("RegulationMode")
    if mode == MODE_SCHEDULE:
        return PRESET_SCHEDULE
    if mode == MODE_MANUAL:
        return PRESET_MANUAL
    return None  # comfort has no preset: it only works with a future end time we don't set


def off_payload(serial: str, d: dict[str, Any]) -> dict[str, Any]:
    return {"SerialNumber": serial, "ManualTemperature": d.get("MinTemp", 500), "RegulationMode": MODE_MANUAL, "VacationEnabled": False}


def heat_payload(serial: str) -> dict[str, Any]:
    """HVAC mode 'heat' = follow the programmed schedule."""
    return {"SerialNumber": serial, "RegulationMode": MODE_SCHEDULE, "VacationEnabled": False}  # also cancels a vacation


def manual_payload(serial: str, celsius_value: float) -> dict[str, Any]:
    return {"SerialNumber": serial, "ManualTemperature": int(round(celsius_value * 100)), "RegulationMode": MODE_MANUAL, "VacationEnabled": False}


def apply_optimistic(record: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    """What the thermostat record will look like once the cloud has applied `payload` (shown right away)."""
    new = {**record, **{k: v for k, v in payload.items() if k != "SerialNumber"}}
    if new.get("RegulationMode") == MODE_MANUAL and "ManualTemperature" in new:
        new["SetPointTemp"] = new["ManualTemperature"]
    return new  # in schedule mode the setpoint comes from the schedule, so it is left for the next refresh to fill in
