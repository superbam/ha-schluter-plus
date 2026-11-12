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

# RegulationMode values (see MODE_NAMES above; 4 is vacation, which is only read, never set locally).
MODE_SCHEDULE, MODE_COMFORT, MODE_MANUAL, MODE_VACATION = 1, 2, 3, 4

# --- Local device gateway (hybrid mode) --------------------------------------
# The thermostat keeps a second connection to OJ Electronics' device gateway. With a LAN DNS record that
# points GATEWAY_HOST at Home Assistant, the thermostat connects to the gateway in local_gateway.py instead.
# Protocol knowledge and the gateway code are adapted from peskyAdmin/schluter-local (MIT, see NOTICE).
CONF_LOCAL_MODE = "local_mode"
LOCAL_OFF = "off"      # cloud only (default; nothing listens on the network)
LOCAL_RELAY = "relay"  # serve Home Assistant locally AND relay to OJ's cloud, so the Schluter app keeps working
LOCAL_ONLY = "local"   # serve locally only; the thermostat never reaches OJ's cloud
LOCAL_MODES = (LOCAL_OFF, LOCAL_RELAY, LOCAL_ONLY)
GATEWAY_HOST = "na-thermos.ojelectronics.com"
GATEWAY_PORT = 9533  # fixed: the thermostat firmware dials this port
# OJ's real gateway, reached by IP so the DNS record does not loop back to us. If OJ moves it, relay mode can't
# reach the cloud and serves the thermostat locally instead until this is updated.
UPSTREAM_GATEWAY_IP = "52.165.43.242"
DEVICE_TEMP_SCALE = 200  # device setpoints are Celsius x200; the cloud API (and this integration) use x100
EPOCH_2000 = 946684800   # device timestamps are unix seconds minus this
# Fields the thermostat reports itself and that therefore override the cloud's copy while it is connected locally.
LOCAL_FIELDS = ("Online", "Room", "RegulationMode", "ManualTemperature", "ComfortTemperature", "SetPointTemp", "Temperature", "Heating")
