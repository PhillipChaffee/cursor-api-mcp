"""Tests for server config and tool registration modes."""

from __future__ import annotations

import asyncio

import pytest

from cursor_api_mcp.config import ServerConfig
from cursor_api_mcp.server import build_server


def test_read_only_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CURSOR_API_READ_ONLY", "true")
    assert ServerConfig.from_env().read_only is True


def test_read_only_cli_flag_overrides_unset_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CURSOR_API_READ_ONLY", raising=False)
    assert ServerConfig.from_env(read_only_flag=True).read_only is True


def test_read_only_false_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CURSOR_API_READ_ONLY", raising=False)
    assert ServerConfig.from_env().read_only is False


def test_read_only_server_omits_write_tools() -> None:
    read_only = build_server(ServerConfig(read_only=True))
    full = build_server(ServerConfig(read_only=False))

    read_names = {tool.name for tool in asyncio.run(read_only.list_tools())}
    full_names = {tool.name for tool in asyncio.run(full.list_tools())}

    assert "list_agents" in read_names
    assert "create_agent" not in read_names
    assert "delete_agent" not in read_names
    assert "create_agent" in full_names
    assert "delete_agent" in full_names
    assert read_names < full_names
