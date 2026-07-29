"""Tests for server config and tool registration modes."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

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


def test_get_daily_usage_rejects_page_without_page_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from cursor_api_mcp.tools import read as read_mod

    mock_client = MagicMock()
    monkeypatch.setattr(read_mod, "client", lambda: mock_client)
    server = build_server(ServerConfig(read_only=True))
    result = asyncio.run(
        server.call_tool(
            "get_daily_usage_data",
            {"start_date_ms": 1, "end_date_ms": 2, "page": 1},
        )
    )
    structured = result.structured_content
    assert isinstance(structured, dict)
    assert structured["error"] is True
    assert "page_size" in structured["message"]
    mock_client.post_json.assert_not_called()


def test_read_only_server_omits_write_tools() -> None:
    read_only = build_server(ServerConfig(read_only=True))
    full = build_server(ServerConfig(read_only=False))

    read_names = {tool.name for tool in asyncio.run(read_only.list_tools())}
    full_names = {tool.name for tool in asyncio.run(full.list_tools())}

    assert "list_agents" in read_names
    assert "download_agent_artifact" in read_names
    assert "stream_agent_run" in read_names
    assert "get_team_analytics" in read_names
    assert "list_ai_code_commits" in read_names
    assert "list_bugbot_repos" in read_names
    assert "list_private_workers" in read_names
    assert "get_organization_pooled_usage" in read_names
    assert "create_agent" not in read_names
    assert "delete_agent" not in read_names
    assert "trigger_bugbot_review" not in read_names
    assert "add_organization_group_members" not in read_names
    assert "create_agent" in full_names
    assert "delete_agent" in full_names
    assert "trigger_bugbot_review" in full_names
    assert "add_organization_group_members" in full_names
    assert read_names < full_names


def test_team_analytics_rejects_unknown_metric(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from cursor_api_mcp.tools import analytics as analytics_mod

    mock_client = MagicMock()
    monkeypatch.setattr(analytics_mod, "client", lambda: mock_client)
    server = build_server(ServerConfig(read_only=True))
    result = asyncio.run(
        server.call_tool("get_team_analytics", {"metric": "not-a-metric"})
    )
    structured = result.structured_content
    assert isinstance(structured, dict)
    assert structured["error"] is True
    assert "Allowed" in structured["message"]
    mock_client.get.assert_not_called()


def test_download_agent_artifact_passes_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from cursor_api_mcp.tools import read as read_mod

    mock_client = MagicMock()
    mock_client.get.return_value = {"url": "https://signed.example/a"}
    monkeypatch.setattr(read_mod, "client", lambda: mock_client)
    server = build_server(ServerConfig(read_only=True))
    result = asyncio.run(
        server.call_tool(
            "download_agent_artifact",
            {"agent_id": "bc-1", "path": "artifacts/shot.png"},
        )
    )
    structured = result.structured_content
    assert isinstance(structured, dict)
    assert structured["url"] == "https://signed.example/a"
    mock_client.get.assert_called_once_with(
        "/v1/agents/bc-1/artifacts/download",
        params={"path": "artifacts/shot.png"},
    )


def test_conversation_insights_requires_include(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from cursor_api_mcp.tools import analytics as analytics_mod

    mock_client = MagicMock()
    monkeypatch.setattr(analytics_mod, "client", lambda: mock_client)
    server = build_server(ServerConfig(read_only=True))
    result = asyncio.run(
        server.call_tool("get_team_analytics", {"metric": "conversation-insights"})
    )
    structured = result.structured_content
    assert isinstance(structured, dict)
    assert structured["error"] is True
    assert "include" in structured["message"]
    mock_client.get.assert_not_called()


def test_org_daily_usage_rejects_page_without_page_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from cursor_api_mcp.tools import org as org_mod

    mock_client = MagicMock()
    monkeypatch.setattr(org_mod, "client", lambda: mock_client)
    server = build_server(ServerConfig(read_only=True))
    result = asyncio.run(
        server.call_tool(
            "get_organization_daily_usage_data",
            {
                "organization_id": "org_1",
                "start_date_ms": 1,
                "end_date_ms": 2,
                "page": 1,
            },
        )
    )
    structured = result.structured_content
    assert isinstance(structured, dict)
    assert structured["error"] is True
    assert "page_size" in structured["message"]
    mock_client.post_json.assert_not_called()


def test_get_private_worker_rejects_traversal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from cursor_api_mcp.tools import fleet as fleet_mod

    mock_client = MagicMock()
    monkeypatch.setattr(fleet_mod, "client", lambda: mock_client)
    server = build_server(ServerConfig(read_only=True))
    result = asyncio.run(
        server.call_tool(
            "get_private_worker",
            {"worker_id": "../../v1/me"},
        )
    )
    structured = result.structured_content
    assert isinstance(structured, dict)
    assert structured["error"] is True
    assert "path segment" in structured["message"]
    mock_client.get.assert_not_called()
