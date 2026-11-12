"""Read-only: sign in and print what the Schluter API reports for each thermostat.

    python tools/discover.py            # prompts for the email and password
    SCHLUTER_EMAIL=... SCHLUTER_PASSWORD=... python tools/discover.py   # or pass them in the environment

Add -v to print the sign-in steps (no passwords are printed).

Nothing is written to Schluter. Your email and the account's other identifying fields are redacted in the output.
"""
import asyncio
import getpass
import logging
import importlib.util
import json
import os
import sys

import aiohttp

spec = importlib.util.spec_from_file_location("api", os.path.join(os.path.dirname(__file__), "..", "custom_components", "schluter_plus", "api.py"))
REDACT = {"Email", "SerialNumber", "DistributerId", "Support"}


def load_api():
    # api.py imports package-relative constants, so stub them for standalone use
    import types
    pkg = types.ModuleType("schluter_plus"); pkg.__path__ = [os.path.join(os.path.dirname(__file__), "..", "custom_components", "schluter_plus")]
    sys.modules["schluter_plus"] = pkg
    import importlib
    return importlib.import_module("schluter_plus.api")


async def main():
    api = load_api()
    async with aiohttp.ClientSession() as s:
        email = os.environ.get("SCHLUTER_EMAIL") or input("Schluter email: ").strip()
        password = os.environ.get("SCHLUTER_PASSWORD") or getpass.getpass("Schluter password: ")
        client = api.SchluterClient(s, email, password)
        data = await client.async_get_thermostats()
    for serial, t in data.items():
        print(f"--- {t.get('Room')} (serial ending {serial[-4:]})")
        for k in sorted(t):
            print(f"  {k}: {'<redacted>' if k in REDACT else json.dumps(t[k])}")


if "-v" in sys.argv:
    logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    logging.getLogger("asyncio").setLevel(logging.WARNING)
asyncio.run(main())
