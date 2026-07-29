"""Unit tests for the Cursor API client helpers."""

from __future__ import annotations

import base64

import httpx
import pytest

from cursor_api_mcp.client import CursorApiClient, CursorApiError


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
        return httpx.Response(
            403,
            json={"error": "Forbidden", "message": "Enterprise access required"},
        )

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    client = CursorApiClient(api_key="crsr_test")
    with pytest.raises(CursorApiError, match="Enterprise access required") as exc_info:
        client.get("/teams/members")
    assert exc_info.value.status_code == 403


def test_error_response_non_dict_json(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(self: httpx.Client, method: str, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(500, json=["unexpected", "shape"])

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    client = CursorApiClient(api_key="crsr_test")
    with pytest.raises(CursorApiError, match="unexpected") as exc_info:
        client.get("/v1/me")
    assert exc_info.value.status_code == 500


def test_get_text(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class RecordingClient:
        def __init__(self, **kwargs: object) -> None:
            captured["client_kwargs"] = kwargs

        def __enter__(self) -> RecordingClient:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def get(self, url: str, **kwargs: object) -> httpx.Response:
            captured["url"] = url
            captured["headers"] = kwargs.get("headers")
            return httpx.Response(200, text="event: done\ndata: {}\n\n")

    monkeypatch.setattr(httpx, "Client", RecordingClient)
    client = CursorApiClient(api_key="crsr_test")
    text = client.get_text("/v1/agents/bc-1/runs/run-1/stream")
    assert "event: done" in text
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Accept"] == "text/event-stream"
    client_kwargs = captured["client_kwargs"]
    assert isinstance(client_kwargs, dict)
    assert client_kwargs.get("follow_redirects") is True


def test_get_rejects_path_traversal(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_request(self: httpx.Client, method: str, url: str, **kwargs: object) -> httpx.Response:
        raise AssertionError("HTTP request should not be sent for unsafe paths")

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    client = CursorApiClient(api_key="crsr_test")
    with pytest.raises(ValueError, match="\\.\\."):
        client.get("/organizations/groups/../../../teams/members")


def test_delete_and_patch_methods(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_request(self: httpx.Client, method: str, url: str, **kwargs: object) -> httpx.Response:
        calls.append(method)
        if method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(200, json={"patched": True})

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    client = CursorApiClient(api_key="crsr_test")
    assert client.delete("/v1/agents/bc-1") == {"ok": True, "status_code": 204}
    assert client.patch_json("/teams/groups/g1", body={"name": "x"}) == {"patched": True}
    assert calls == ["DELETE", "PATCH"]
