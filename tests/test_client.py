"""Unit tests for the Cursor API client helpers."""

from __future__ import annotations

import base64

import httpx
import pytest

from cursor_api_readonly_mcp.client import CursorApiClient, CursorApiError


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    with pytest.raises(ValueError, match="CURSOR_API_KEY"):
        CursorApiClient()


def test_get_sends_basic_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_request(self: httpx.Client, method: str, url: str, **kwargs: object) -> httpx.Response:
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = kwargs.get("headers")
        captured["params"] = kwargs.get("params")
        return httpx.Response(200, json={"ok": True})

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    client = CursorApiClient(api_key="crsr_test")
    assert client.get("/v1/me", params={"unused": None, "keep": "1"}) == {"ok": True}

    expected = base64.b64encode(b"crsr_test:").decode()
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Authorization"] == f"Basic {expected}"
    assert captured["method"] == "GET"
    assert captured["url"] == "https://api.cursor.com/v1/me"
    assert captured["params"] == {"keep": "1"}


def test_error_response_raises_cursor_api_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(self: httpx.Client, method: str, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(403, json={"error": "Forbidden", "message": "Enterprise access required"})

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    client = CursorApiClient(api_key="crsr_test")
    with pytest.raises(CursorApiError, match="Enterprise access required") as exc_info:
        client.get("/teams/members")
    assert exc_info.value.status_code == 403
