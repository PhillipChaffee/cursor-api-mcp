"""HTTP client for the Cursor API."""

from __future__ import annotations

import base64
import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "https://api.cursor.com"
DEFAULT_TIMEOUT_SECONDS = 60.0


class CursorApiError(RuntimeError):
    """Raised when the Cursor API returns a non-success status."""

    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        super().__init__(f"Cursor API {status_code}: {message}")


class CursorApiClient:
    """Thin Basic-auth client for Cursor HTTP APIs."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        resolved_key = api_key or os.environ.get("CURSOR_API_KEY")
        if not resolved_key:
            raise ValueError(
                "CURSOR_API_KEY is required. Create a key at https://cursor.com/dashboard/api"
            )
        resolved_base = base_url or os.environ.get("CURSOR_API_BASE_URL") or DEFAULT_BASE_URL
        self._base_url = resolved_base.rstrip("/")
        token = base64.b64encode(f"{resolved_key}:".encode()).decode()
        self._headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
        }
        self._timeout = timeout_seconds

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """GET a Cursor API path and return decoded JSON."""
        return self._request("GET", path, params=params)

    def post_json(
        self,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """POST JSON to a Cursor API path."""
        return self._request("POST", path, params=params, json_body=body or {})

    def patch_json(
        self,
        path: str,
        *,
        body: dict[str, Any] | None = None,
    ) -> Any:
        """PATCH JSON to a Cursor API path."""
        return self._request("PATCH", path, json_body=body or {})

    def delete(
        self,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """DELETE a Cursor API path."""
        return self._request("DELETE", path, params=params, json_body=body)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self._base_url}{path if path.startswith('/') else f'/{path}'}"
        clean_params = (
            {key: value for key, value in params.items() if value is not None}
            if params
            else None
        )
        with httpx.Client(timeout=self._timeout) as client:
            response = client.request(
                method,
                url,
                headers=self._headers,
                params=clean_params,
                json=json_body,
            )
        if response.status_code >= 400:
            message = response.text
            try:
                payload = response.json()
                message = str(
                    payload.get("message")
                    or payload.get("error")
                    or payload
                )
            except ValueError:
                pass
            raise CursorApiError(response.status_code, message)
        if response.status_code == 204 or not response.content:
            return {"ok": True, "status_code": response.status_code}
        return response.json()
