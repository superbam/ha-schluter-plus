"""Offline tests of the climate mapping (no Home Assistant needed)."""
import importlib.util, os

spec = importlib.util.spec_from_file_location("helpers", os.path.join(os.path.dirname(__file__), "..", "custom_components", "schluter_plus", "helpers.py"))
h = importlib.util.module_from_spec(spec); spec.loader.exec_module(h)

sched = {"RegulationMode": 1, "SetPointTemp": 2333, "MinTemp": 500, "MaxTemp": 4000, "ManualTemperature": 1722}
manual_low = {"RegulationMode": 3, "SetPointTemp": 500, "MinTemp": 500, "MaxTemp": 4000}
manual_warm = {"RegulationMode": 3, "SetPointTemp": 2500, "MinTemp": 500, "MaxTemp": 4000}
low_schedule = {"RegulationMode": 1, "SetPointTemp": 500, "MinTemp": 500}   # a schedule that sets the minimum is NOT "off"

assert h.celsius(2333) == 23.33 and h.min_temp(sched) == 5.0 and h.max_temp(sched) == 40.0
assert not h.is_off(sched) and h.is_off(manual_low) and not h.is_off(manual_warm) and not h.is_off(low_schedule)
assert h.preset(sched) == "schedule" and h.preset(manual_warm) == "manual" and h.preset({"RegulationMode": 2}) is None
assert h.off_payload("S1", sched) == {"SerialNumber": "S1", "ManualTemperature": 500, "RegulationMode": 3, "VacationEnabled": False}
assert h.heat_payload("S1") == {"SerialNumber": "S1", "RegulationMode": 1, "VacationEnabled": False}
assert h.manual_payload("S1", 21.5) == {"SerialNumber": "S1", "ManualTemperature": 2150, "RegulationMode": 3, "VacationEnabled": False}
print("helper tests passed")
