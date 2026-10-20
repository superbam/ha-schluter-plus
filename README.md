# Schluter DITRA-HEAT Plus (Home Assistant)

Adds what Home Assistant's built-in **Schluter** integration doesn't expose for DITRA-HEAT-E-WiFi thermostats:

| Entity (per thermostat) | What it does |
|---|---|
| **Mode** (select) | schedule / comfort / manual / vacation. Setting it back to *schedule* returns the thermostat to its programmed schedule. |
| **Measured load** (sensor, W) | The load the thermostat reports. |
| **Programmed load** (sensor, W) | The load configured in the thermostat. |
| **Heating**, **Online**, **Vacation mode** (binary sensors) | State flags. |
| **Error code** (sensor) | Diagnostic. |

It is additive: it signs in to the same Schluter cloud API but does not replace or modify the built-in integration, so your existing `climate` entities keep working.

> **Status: v0.1.0, unverified against live hardware.** The API client is covered by offline tests, but the mode numbers in `const.py` (`MODE_NAMES`) are unconfirmed (see below). Don't automate on the mode selector until you've checked them.

## Install (HACS)

1. HACS -> three dots -> **Custom repositories** -> add `https://github.com/superbam/ha-schluter-plus`, category **Integration**.
2. Download it, restart Home Assistant.
3. Settings -> Devices & services -> **Add integration** -> *Schluter DITRA-HEAT Plus* -> sign in with your DITRA-HEAT account.

## Verifying mode numbers

The `aioschluter` library labels `RegulationMode` 1=schedule, 2=manual, 3=away, yet its own set-temperature call sends 3 together with a manual temperature. Run the read-only discovery while a thermostat is in a known state and compare:

    SCHLUTER_EMAIL=... SCHLUTER_PASSWORD=... python tools/discover.py

then change the mode in the Schluter app/site and run it again. Update `MODE_NAMES` in `const.py` to match what you see.

## Development

    python3 -m venv .venv && .venv/bin/pip install aiohttp
    .venv/bin/python tests/test_api.py

Credentials are never committed (`.env` and discovery output are gitignored).
