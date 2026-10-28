from __future__ import annotations

import os
from typing import Any, Literal

import httpx

from cursor_api_mcp.client import DEFAULT_TIMEOUT_SECONDS, CursorApiError

AUTOMATIONS_ORIGIN = "https://api2.cursor.sh"


def _token(value: str) -> str:
    value = value.strip()
    if value.lower().startswith("bearer "):
        value = value[7:].strip()
    if (
        not value
        or value.lower() == "bearer"
        or any(ord(char) < 33 or ord(char) > 126 for char in value)
    ):
        raise ValueError("Invalid automation credential")
    return value


class AutomationsClient:
    """Resolve a bearer token in memory for one tool invocation."""

    def __init__(self, api_key: str | None = None) -> None:
        resolved_key = api_key if api_key is not None else os.environ.get("CURSOR_API_KEY")
        if not resolved_key:
            raise ValueError("CURSOR_API_KEY is required for automation access")
        self._token = _token(resolved_key)
        self._needs_exchange = self._token.startswith(("key_", "crsr_"))

    def call(
        self,
        method: Literal["GetAutomation", "UpdateAutomation"],
        body: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a fixed automation RPC without redirects or retries."""
        if self._needs_exchange:
            payload = self._post("/auth/exchange_user_api_key", {})
            access_token = payload.get("accessToken")
            if not isinstance(access_token, str):
                raise ValueError("Automation token exchange returned no access token")
            self._token = _token(access_token)
            self._needs_exchange = False
        return self._post(f"/aiserver.v1.AutomationsService/{method}", body)

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        operation = path.rsplit("/", 1)[-1]
        failure = f"Automation {operation} failed."
        if operation == "UpdateAutomation":
            failure += " The write may have been applied; inspect it before retrying."
        try:
            with httpx.Client(
                timeout=DEFAULT_TIMEOUT_SECONDS, follow_redirects=False
            ) as http_client:
                response = http_client.post(
                    AUTOMATIONS_ORIGIN + path,
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Content-Type": "application/json",
                        "Connect-Protocol-Version": "1",
                    },
                    json=body,
                )
        except httpx.HTTPError:
            raise RuntimeError(failure + " Transport error.") from None
        if not response.is_success:
            raise CursorApiError(response.status_code, failure)
        try:
            payload = response.json()
        except ValueError:
            raise ValueError(failure + " Invalid JSON response.") from None
        if not isinstance(payload, dict):
            raise ValueError(failure + " Expected a JSON object.")
        return payload
