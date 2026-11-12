"""Pure functions mapping the Schluter API record to Home Assistant climate concepts (testable without HA)."""
from __future__ import annotations

from typing import Any

from .const import LOCAL_FIELDS, MODE_COMFORT, MODE_MANUAL, MODE_SCHEDULE

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


# Keys a command may carry and still be sent to the thermostat locally. Anything else (comfort/vacation/schedule
# edits, which need fields the local link doesn't decode yet) goes through the cloud.
_LOCAL_PAYLOAD_KEYS = {"SerialNumber", "RegulationMode", "ManualTemperature", "VacationEnabled"}


def local_command(payload: dict[str, Any], record: dict[str, Any]) -> tuple[int, int | None] | None:
    """Translate a cloud-style payload into the local gateway's (mode, setpoint in Celsius x200), or None if it can't go local."""
    if not set(payload) <= _LOCAL_PAYLOAD_KEYS or record.get("VacationEnabled"):
        return None  # a vacation can only be cancelled through the cloud
    mode = payload.get("RegulationMode")
    if mode == MODE_SCHEDULE and "ManualTemperature" not in payload:
        return MODE_SCHEDULE, None
    if mode == MODE_MANUAL:
        manual = payload.get("ManualTemperature")
        return MODE_MANUAL, None if manual is None else int(manual) * 2
    return None


def merge_local(cloud: dict[str, Any], local: dict[str, Any] | None, connected: bool) -> dict[str, Any]:
    """The thermostat's own report wins for what it reports (while it is connected locally); the cloud supplies the rest."""
    if not local or not connected:
        return cloud
    return {**cloud, **{k: v for k, v in local.items() if k in LOCAL_FIELDS}}
