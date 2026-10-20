# Schluter DITRA-HEAT Plus (Home Assistant)

A full replacement for Home Assistant's built-in **Schluter** integration for DITRA-HEAT-E-WiFi thermostats, adding what it doesn't expose:

| Entity (per thermostat) | What it does |
|---|---|
| **Climate** (the thermostat card) | Current and target temperature, idle/heating, and the same `temperature` / `current_temperature` / `hvac_action` attributes as the built-in. **Heat** = follow the schedule, **Off** = park the floor at the minimum (frost protection only), presets *schedule* / *manual*. Setting a temperature switches to manual at that temperature. |
| **Mode** (select) | schedule / comfort / manual. Setting it to *schedule* returns the thermostat to its programmed schedule. |
| **Manual temperature** (number) | The setpoint used in manual mode. Set it low (down to 5 °C / 41 °F) and select *manual* to effectively shut a floor off while nobody is home. |
| **Element load (measured)** (sensor, W) | The heating element's load as the thermostat measures it (`LoadMeasuredWatt`). This is a *rating*, not consumption: it reads the same whether or not the floor is heating. Multiply it by the **Heating** state (e.g. in PowerCalc) to get power draw. |
| **Element load (programmed)** (sensor, W) | The load typed into the thermostat (the 100 W factory default). Read-only: the cloud ignores writes to it. Disabled by default. |
| **Load measuring** (binary sensor) | Whether the thermostat is measuring its own load. If it turns off, Schluter's own kWh reports fall back to the 100 W default and come out far too low. |
| **Heating**, **Online**, **Vacation mode** (binary sensors) | State flags. |
| **Error code** (sensor) | Diagnostic. |

It signs in to the same Schluter cloud API. You can run it next to the built-in integration, or replace the built-in one (see below).

> **Status: v0.3.0.** The mode numbers were verified against a live DITRA-HEAT-E-WiFi (1 = schedule, 3 = manual, 2 = comfort; the `aioschluter` library labels them wrongly). Changing the mode and the manual temperature were tested on a real thermostat and restored.

### Away / return pattern

1. Leaving: set **Manual temperature** low, then set **Mode** to *manual*.
2. Returning: set **Mode** to *schedule*. The schedule resumes, and the stored manual temperature is left as it was.

## Install (HACS)

1. HACS -> three dots -> **Custom repositories** -> add `https://github.com/superbam/ha-schluter-plus`, category **Integration**.
2. Download it, restart Home Assistant.
3. Settings -> Devices & services -> **Add integration** -> *Schluter DITRA-HEAT Plus* -> sign in with your DITRA-HEAT account.

## Replacing the built-in integration

1. Install and set up this integration (below). It creates `climate.schluter_<room>` entities next to the built-in `climate.<room>` ones.
2. Check that they behave: temperature, heating state, and **off** / **heat** (schedule).
3. Settings -> Devices & services -> **Schluter** (the built-in) -> three dots -> **Disable**.
4. Rename the new climate entities to the old ids (entity settings -> *Entity ID*) so dashboards, automations and the recorder history keep working.

Off means manual mode at the thermostat's minimum temperature (5 C / 41 F), so the floor won't heat; heat means "resume the programmed schedule" (and cancels a vacation).

## Credentials

You enter the email and password in Home Assistant's own UI (a masked field); they're stored in HA's config storage, never in this repository or a file you edit. If the password changes, HA prompts you to sign in again, or use the integration's *Reconfigure* menu. `tools/check_no_secrets.sh` (installed as a git pre-commit hook) refuses to commit anything that looks like a credential.

## Trademarks and affiliation

This is an unofficial, community project. It is not made, endorsed or supported by Schluter-Systems. "Schluter", "DITRA" and "DITRA-HEAT" and the Schluter logo are trademarks of Schluter Systems L.P.; the logo files in `custom_components/schluter_plus/brand/` are the same images Home Assistant's brand service already serves for its built-in Schluter integration and are used here only to identify the product this integration works with. They are not covered by this project's MIT license. If Schluter asks for them to be removed, they will be.

## Development

    python3 -m venv .venv && .venv/bin/pip install aiohttp
    .venv/bin/python tests/test_api.py

Credentials are never committed (`.env` and discovery output are gitignored).
