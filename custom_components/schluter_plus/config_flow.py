"""UI setup, re-authentication and reconfiguration: the account email and password are entered in Home Assistant."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorConfig, TextSelectorType

from .api import InvalidAuth, SchluterClient, SchluterError
from .const import DOMAIN

PASSWORD = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD, autocomplete="current-password"))
EMAIL = TextSelector(TextSelectorConfig(type=TextSelectorType.EMAIL, autocomplete="username"))


class SchluterPlusConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, email: str, password: str) -> str | None:
        """Return an error key, or None if the login works."""
        try:
            await SchluterClient(async_get_clientsession(self.hass), email, password).async_login()
        except InvalidAuth:
            return "invalid_auth"
        except SchluterError:
            return "cannot_connect"
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()
            if not (error := await self._validate(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])):
                return self.async_create_entry(title=user_input[CONF_EMAIL], data=user_input)
            errors["base"] = error
        schema = vol.Schema({vol.Required(CONF_EMAIL): EMAIL, vol.Required(CONF_PASSWORD): PASSWORD})
        return self.async_show_form(step_id="user", data_schema=self.add_suggested_values_to_schema(schema, user_input), errors=errors)

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> ConfigFlowResult:
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """The stored password stopped working: ask for it again."""
        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not (error := await self._validate(entry.data[CONF_EMAIL], user_input[CONF_PASSWORD])):
                return self.async_update_reload_and_abort(entry, data_updates={CONF_PASSWORD: user_input[CONF_PASSWORD]})
            errors["base"] = error
        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): PASSWORD}),
            description_placeholders={"email": entry.data[CONF_EMAIL]},
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Change the email or password from the integration's menu."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not (error := await self._validate(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])):
                return self.async_update_reload_and_abort(entry, data_updates=user_input)
            errors["base"] = error
        schema = vol.Schema({vol.Required(CONF_EMAIL, default=entry.data[CONF_EMAIL]): EMAIL, vol.Required(CONF_PASSWORD): PASSWORD})
        return self.async_show_form(step_id="reconfigure", data_schema=schema, errors=errors)
