"""Thin async client for the Schluter DITRA-HEAT-E-WiFi cloud API."""
from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError, ClientSession

from .const import (
    API_APPLICATION_ID,
    API_AUTH_URL,
    API_THERMOSTAT_URL,
    API_THERMOSTATS_URL,
)

_LOGGER = logging.getLogger(__name__)


class SchluterError(Exception):
    """Any API failure."""


class InvalidAuth(SchluterError):
    """Bad credentials or an expired session."""


class SchluterClient:
    """Signs in, caches the session id and re-signs-in when it expires."""

    def __init__(self, session: ClientSession, email: str, password: str) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._session_id: str | None = None

    async def async_login(self) -> str:
        try:
            async with self._session.post(
                API_AUTH_URL,
                json={"Email": self._email, "Password": self._password, "Application": API_APPLICATION_ID},
            ) as resp:
                if resp.status == 401:
                    raise InvalidAuth("Invalid username or password")
                if resp.status != 200:
                    raise SchluterError(f"Login failed: HTTP {resp.status}")
                data = await resp.json()
        except ClientError as err:
            raise SchluterError(f"Cannot reach Schluter: {err}") from err
        if not data.get("SessionId"):
            raise InvalidAuth("Invalid username or password")
        self._session_id = data["SessionId"]
        return self._session_id

    async def _request(self, method: str, url: str, *, params: dict | None = None, json: Any = None) -> Any:
        for attempt in (1, 2):
            if not self._session_id:
                await self.async_login()
            try:
                async with self._session.request(
                    method, url, params={"sessionId": self._session_id, **(params or {})}, json=json
                ) as resp:
                    if resp.status == 401 and attempt == 1:
                        self._session_id = None  # expired: sign in again once
                        continue
                    if resp.status == 401:
                        raise InvalidAuth("Session rejected")
                    if resp.status != 200:
                        raise SchluterError(f"HTTP {resp.status} from {url}")
                    return await resp.json()
            except ClientError as err:
                raise SchluterError(f"Cannot reach Schluter: {err}") from err
        raise SchluterError("unreachable")

    async def async_get_thermostats(self) -> dict[str, dict[str, Any]]:
        """Return every thermostat's raw API record, keyed by serial number."""
        data = await self._request("GET", API_THERMOSTATS_URL)
        return {t["SerialNumber"]: t for g in data.get("Groups", []) for t in g.get("Thermostats", [])}

    async def async_update_thermostat(self, serial: str, fields: dict[str, Any]) -> None:
        """POST changed fields for one thermostat."""
        data = await self._request("POST", API_THERMOSTAT_URL, params={"serialnumber": serial}, json=fields)
        if not data.get("Success"):
            raise SchluterError(f"Schluter rejected the change: {data}")

    async def async_set_mode(self, serial: str, mode: int) -> None:
        await self.async_update_thermostat(serial, {"SerialNumber": serial, "RegulationMode": mode})
