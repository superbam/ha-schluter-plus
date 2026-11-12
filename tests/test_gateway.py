"""Offline tests for the local gateway: a fake thermostat connects over TLS, no Home Assistant needed.

Run with Python 3.12+:  python tests/test_gateway.py   (needs the `openssl` command line tool)
"""
import asyncio
import importlib
import os
import ssl
import subprocess
import sys
import tempfile
import types

PKG = os.path.join(os.path.dirname(__file__), "..", "custom_components", "schluter_plus")


def load():
    pkg = types.ModuleType("schluter_plus"); pkg.__path__ = [PKG]
    sys.modules["schluter_plus"] = pkg
    for name in ("const", "helpers", "local_gateway"):
        sys.modules.pop(f"schluter_plus.{name}", None)
    return importlib.import_module("schluter_plus.local_gateway"), importlib.import_module("schluter_plus.helpers")


def self_signed(dirpath):
    cert, key = os.path.join(dirpath, "c.pem"), os.path.join(dirpath, "k.pem")
    subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cert, "-days", "2", "-subj", "/CN=test"],
                   check=True, capture_output=True)
    return cert, key


def varint(v):
    out = bytearray()
    while True:
        b = v & 0x7F; v >>= 7
        out.append(b | (0x80 if v else 0))
        if not v:
            return bytes(out)


def enc(gw, field, value):
    return gw._encode(field, value)


def msg(gw, *pairs):
    return b"".join(enc(gw, f, v) for f, v in pairs)


async def read(gw, reader):
    return gw.parse(await asyncio.wait_for(gw.LocalGateway._read_frame(reader), 5))


async def run():
    gw, helpers = load()
    tmp = tempfile.mkdtemp()
    cert, key = self_signed(tmp)
    seen = []
    g = gw.LocalGateway(cert, key, relay=False, on_state=lambda serial, fields: seen.append((serial, fields)), port=0)
    g._build_contexts()
    g._server = await asyncio.start_server(g._handle, "127.0.0.1", 0, ssl=g._server_ctx)
    port = g._server.sockets[0].getsockname()[1]

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    reader, writer = await asyncio.open_connection("127.0.0.1", port, ssl=ctx)

    # login -> acknowledged, thermostat reported online
    writer.write(gw._frame(msg(gw, (1, 1), (6, msg(gw, (1, b"a@b.c"), (2, b"SER1"), (3, 7))))))
    await writer.drain()
    top = await read(gw, reader)
    assert top[1] == [1] and top[3] == [1], top
    assert ("SER1", {"Online": True}) in seen, seen
    assert g.connected_serials == {"SER1"}

    # full state upload: schedule mode, 20 C permanent hold setpoint (x200 = 4000), target 21 C, room name
    state = msg(gw, (1, 5000), (2, 1), (5, msg(gw, (1, 4000))))
    writer.write(gw._frame(msg(gw, (1, 2), (2, 4), (7, msg(gw, (2, b"Guest"), (9, 4200))), (8, b"SCHED"), (9, state))))
    await writer.drain()
    top = await read(gw, reader)
    assert top[3] == [1]
    fields = {k: v for _, f in seen for k, v in f.items()}
    assert fields["RegulationMode"] == 1 and fields["ManualTemperature"] == 2000 and fields["Room"] == "Guest" and fields["SetPointTemp"] == 2100, fields
    await read(gw, reader)  # the configuration message that follows the ack

    # telemetry heartbeat: floor 21.5 C, heating
    writer.write(gw._frame(msg(gw, (1, 3), (15, msg(gw, (1, 2150), (2, 1))))))
    await writer.drain()
    await read(gw, reader)
    assert seen[-1] == ("SER1", {"Temperature": 2150, "Heating": True}), seen[-1]

    # command: permanent hold at 22 C -> the thermostat receives mode 3 with 9.5.1 = 4400, schedule echoed back
    await g.queue_set("SER1", 3, 4400)
    cmd = await read(gw, reader)
    assert cmd[5] == [1] and cmd[8] == [b"SCHED"], cmd
    st = gw.parse(cmd[9][0])
    assert st[2] == [3] and gw.parse(st[5][0])[1] == [4400], st

    # back to schedule changes only the mode; everything else is copied from the thermostat's last reported state
    # (this fake thermostat never reported the 22 C hold, so the stored hold setpoint is still its original 20 C)
    await g.queue_set("SER1", 1, None)
    st = gw.parse((await read(gw, reader))[9][0])
    assert st[2] == [1] and gw.parse(st[5][0])[1] == [4000], st

    # disconnect -> offline
    writer.close()
    for _ in range(50):
        if seen[-1] == ("SER1", {"Online": False}):
            break
        await asyncio.sleep(0.05)
    assert seen[-1] == ("SER1", {"Online": False}) and not g.connected_serials, seen[-3:]
    await g.stop()

    # ---- helpers: which commands may go local, and how the local report overlays the cloud
    rec = {"RegulationMode": 1, "VacationEnabled": False}
    assert helpers.local_command(helpers.heat_payload("S"), rec) == (1, None)
    assert helpers.local_command(helpers.manual_payload("S", 22), rec) == (3, 4400)
    assert helpers.local_command(helpers.off_payload("S", {"MinTemp": 500}), rec) == (3, 1000)
    assert helpers.local_command({"RegulationMode": 2, "ComfortTemperature": 2500}, rec) is None      # comfort stays on the cloud
    assert helpers.local_command(helpers.heat_payload("S"), {"VacationEnabled": True}) is None        # vacation can only be cancelled via the cloud
    cloud = {"Room": "Guest", "RegulationMode": 1, "LoadMeasuredWatt": 690, "Heating": False}
    assert helpers.merge_local(cloud, {"Heating": True, "Temperature": 2150, "Bogus": 1}, True) == {**cloud, "Heating": True, "Temperature": 2150}
    assert helpers.merge_local(cloud, {"Heating": True}, False) is cloud
    print("gateway tests passed")

asyncio.run(run())
