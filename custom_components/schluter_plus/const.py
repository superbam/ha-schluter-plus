"""Constants for Schluter DITRA-HEAT Plus."""
from datetime import timedelta

DOMAIN = "schluter_plus"
API_BASE_URL = "https://ditra-heat-e-wifi.schluter.com"
API_AUTH_URL = f"{API_BASE_URL}/api/authenticate/user"
API_THERMOSTATS_URL = f"{API_BASE_URL}/api/thermostats"
API_THERMOSTAT_URL = f"{API_BASE_URL}/api/thermostat"
API_APPLICATION_ID = 7  # the same application id the official site and app use

SCAN_INTERVAL = timedelta(minutes=5)

# RegulationMode values, verified against a live DITRA-HEAT-E-WiFi (Oct 2026):
#   1 = schedule: the setpoint follows the weekly schedule.
#   3 = manual:   the setpoint is ManualTemperature (aioschluter's own set-temperature call uses this).
#   2 = comfort:  a temporary boost to ComfortTemperature until ComfortEndTime; once that time has
#                 passed the thermostat keeps its previous setpoint.
# (aioschluter's constants label these 1/2/3 as schedule/manual/away, which is wrong.)
# Vacation is separate: VacationEnabled plus VacationBeginDay/EndDay/Temperature.
MODE_NAMES = {
    1: "schedule",
    2: "comfort",
    3: "manual",
}
