"""Offline tests for the API client: fake Schluter server, no Home Assistant needed."""
import asyncio
import importlib
import os
import sys
import types

from aiohttp import web
from aiohttp.test_utils import TestServer

PKG = os.path.join(os.path.dirname(__file__), "..", "custom_components", "schluter_plus")


def load(server_url):
    pkg = types.ModuleType("schluter_plus"); pkg.__path__ = [PKG]
    sys.modules["schluter_plus"] = pkg
    const = importlib.import_module("schluter_plus.const")
    for name in ("API_AUTH_URL", "API_THERMOSTATS_URL", "API_THERMOSTAT_URL"):
        setattr(const, name, server_url + "/api/" + {"API_AUTH_URL": "authenticate/user", "API_THERMOSTATS_URL": "thermostats", "API_THERMOSTAT_URL": "thermostat"}[name])
    sys.modules.pop("schluter_plus.api", None)
    return importlib.import_module("schluter_plus.api")


def make_app(state):
    async def auth(req):
        body = await req.json()
        state["logins"] += 1
        if body["Password"] != "pw":
            return web.json_response({"SessionId": "", "ErrorCode": 1})
        return web.json_response({"SessionId": f"sess{state['logins']}", "ErrorCode": 0})

    async def thermostats(req):
        if req.query["sessionId"] in state["expired"]:
            return web.Response(status=401)
        return web.json_response({"Groups": [{"Thermostats": [{"SerialNumber": "S1", "Room": "Guest", "RegulationMode": 1, "LoadMeasuredWatt": 690}]}]})

    async def thermostat(req):
        state["posts"].append((req.query["serialnumber"], await req.json()))
        return web.json_response({"Success": True})

    app = web.Application()
    app.add_routes([web.post("/api/authenticate/user", auth), web.get("/api/thermostats", thermostats), web.post("/api/thermostat", thermostat)])
    return app


async def run():
    import aiohttp
    state = {"logins": 0, "expired": set(), "posts": []}
    server = TestServer(make_app(state)); await server.start_server()
    api = load(str(server.make_url("")).rstrip("/"))
    async with aiohttp.ClientSession() as s:
        c = api.SchluterClient(s, "a@b.c", "pw")
        t = await c.async_get_thermostats()
        assert t["S1"]["LoadMeasuredWatt"] == 690 and state["logins"] == 1
        state["expired"].add("sess1")                       # session expires: client must sign in again, once
        t = await c.async_get_thermostats()
        assert state["logins"] == 2, state
        await c.async_set_mode("S1", 1)
        assert state["posts"] == [("S1", {"SerialNumber": "S1", "RegulationMode": 1})], state["posts"]
        bad = api.SchluterClient(s, "a@b.c", "wrong")
        try:
            await bad.async_login(); raise SystemExit("expected InvalidAuth")
        except api.InvalidAuth:
            pass
    await server.close()
    print("api tests passed")

asyncio.run(run())
