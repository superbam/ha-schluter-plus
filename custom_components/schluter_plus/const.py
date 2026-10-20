"""Constants for Schluter DITRA-HEAT Plus."""
from datetime import timedelta

DOMAIN = "schluter_plus"
API_BASE_URL = "https://ditra-heat-e-wifi.schluter.com"
API_AUTH_URL = f"{API_BASE_URL}/api/authenticate/user"
API_THERMOSTATS_URL = f"{API_BASE_URL}/api/thermostats"
API_THERMOSTAT_URL = f"{API_BASE_URL}/api/thermostat"
API_APPLICATION_ID = 7  # the same application id the official site and app use

SCAN_INTERVAL = timedelta(minutes=5)

# RegulationMode values as the API reports them.
#
# UNVERIFIED: aioschluter's constants say 1=schedule, 2=manual, 3=away, but its own
# set-temperature call sends 3 together with ManualTemperature. Confirm against a real
# thermostat (see README, "Verifying mode numbers") and fix this one table.
MODE_NAMES = {
    1: "schedule",
    2: "comfort",
    3: "manual",
    4: "vacation",
}
