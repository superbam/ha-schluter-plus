# Schluter DITRA-HEAT Plus (Home Assistant)

Adds what Home Assistant's built-in **Schluter** integration doesn't expose for DITRA-HEAT-E-WiFi thermostats:

| Entity (per thermostat) | What it does |
|---|---|
| **Mode** (select) | schedule / comfort / manual. Setting it to *schedule* returns the thermostat to its programmed schedule. |
| **Manual temperature** (number) | The setpoint used in manual mode. Set it low (down to 5 °C / 41 °F) and select *manual* to effectively shut a floor off while nobody is home. |
| **Measured load** (sensor, W) | The heating load the thermostat itself measures (`LoadMeasuredWatt`). |
| **Programmed load** (sensor, W) | The load configured in the thermostat. |
| **Heating**, **Online**, **Vacation mode** (binary sensors) | State flags. |
| **Error code** (sensor) | Diagnostic. |

It is additive: it signs in to the same Schluter cloud API but does not replace or modify the built-in integration, so your existing `climate` entities keep working.

> **Status: v0.2.0.** The mode numbers were verified against a live DITRA-HEAT-E-WiFi (1 = schedule, 3 = manual, 2 = comfort; the `aioschluter` library labels them wrongly). Changing the mode and the manual temperature were tested on a real thermostat and restored.

### Away / return pattern

1. Leaving: set **Manual temperature** low, then set **Mode** to *manual*.
2. Returning: set **Mode** to *schedule*. The schedule resumes, and the stored manual temperature is left as it was.

## Install (HACS)

1. HACS -> three dots -> **Custom repositories** -> add `https://github.com/superbam/ha-schluter-plus`, category **Integration**.
2. Download it, restart Home Assistant.
3. Settings -> Devices & services -> **Add integration** -> *Schluter DITRA-HEAT Plus* -> sign in with your DITRA-HEAT account.

## Credentials

You enter the email and password in Home Assistant's own UI (a masked field); they're stored in HA's config storage, never in this repository or a file you edit. If the password changes, HA prompts you to sign in again, or use the integration's *Reconfigure* menu. `tools/check_no_secrets.sh` (installed as a git pre-commit hook) refuses to commit anything that looks like a credential.

## Development

    python3 -m venv .venv && .venv/bin/pip install aiohttp
    .venv/bin/python tests/test_api.py

Credentials are never committed (`.env` and discovery output are gitignored).
