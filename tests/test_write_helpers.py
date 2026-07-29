"""Tests for write-tool JSON helpers and create_agent validation."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from cursor_api_mcp.config import ServerConfig
from cursor_api_mcp.server import build_server
from cursor_api_mcp.tools import write as write_mod
from cursor_api_mcp.tools.write import (
    _parse_json_list,
    _parse_json_object,
    _redact_worker_token_response,
)


def test_parse_json_helpers() -> None:
    assert _parse_json_object(None, field_name="x") is None
    assert _parse_json_object({"a": 1}, field_name="x") == {"a": 1}
    assert _parse_json_list([1], field_name="x") == [1]
    with pytest.raises(ValueError, match="JSON object"):
        _parse_json_object("[1]", field_name="x")


def test_redact_worker_token_response() -> None:
    payload = {"accessToken": "jwt-secret", "userId": 1}
    redacted = _redact_worker_token_response(payload)
    assert redacted["accessToken"] == "[redacted]"
    assert payload["accessToken"] == "jwt-secret"


def _structured(result: Any) -> dict[str, Any]:
    content = getattr(result, "structured_content", None)
    assert isinstance(content, dict)
    return content


async def _create_agent(**kwargs: Any) -> dict[str, Any]:
    server = build_server(ServerConfig(read_only=False))
    return _structured(await server.call_tool("create_agent", kwargs))


def test_create_agent_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = MagicMock()
    mock_client.post_json.return_value = {"ok": True}
    monkeypatch.setattr(write_mod, "client", lambda: mock_client)

    missing_repo = asyncio.run(
        _create_agent(prompt_text="x", pr_url="https://github.com/o/r/pull/1")
    )
    assert missing_repo["error"] is True
    assert "repo_url" in missing_repo["message"]

    clobber = asyncio.run(
        _create_agent(prompt_text="x", extra_json={"prompt": {"images": []}})
    )
    assert clobber["error"] is True
    assert "prompt" in clobber["message"]

    model_clash = asyncio.run(
        _create_agent(
            prompt_text="x",
            model_id="composer-2",
            extra_json={"model": {"params": [{"id": "fast", "value": "true"}]}},
        )
    )
    assert model_clash["error"] is True

    ok = asyncio.run(
        _create_agent(
            prompt_text="x",
            extra_json={
                "model": {"id": "composer-2", "params": [{"id": "fast", "value": "true"}]}
            },
        )
    )
    assert ok == {"ok": True}
    body = mock_client.post_json.call_args.kwargs["body"]
    assert body["model"]["id"] == "composer-2"
    assert mock_client.post_json.call_count == 1
