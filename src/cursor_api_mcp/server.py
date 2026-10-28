"""Cursor API MCP server entrypoint."""

from __future__ import annotations

import argparse

from mcp.server.mcpserver import MCPServer

from cursor_api_mcp.config import ServerConfig
from cursor_api_mcp.tools import (
    register_ai_code_tools,
    register_analytics_tools,
    register_automation_read_tools,
    register_automation_write_tools,
    register_bugbot_read_tools,
    register_bugbot_write_tools,
    register_fleet_tools,
    register_org_read_tools,
    register_org_write_tools,
    register_read_tools,
    register_write_tools,
)


def build_server(config: ServerConfig) -> MCPServer:
    """Construct an MCP server with tools matching ``config``."""
    if not config.read_only:
        mode = "read/write"
        writes = (
            "Write tools can update automations, create/cancel/archive/delete agents, "
            "change team/org settings, and mutate Bugbot config."
        )
    elif config.allow_automation_writes:
        mode = "read-only with automation updates"
        writes = (
            "Only update_automation is enabled among write tools. All other writes are disabled."
        )
    else:
        mode = "read-only"
        writes = "Write tools are disabled in this session."
    mcp = MCPServer(
        "cursor-api",
        instructions=(
            f"Cursor HTTP API MCP ({mode}). "
            "Cloud Agents tools work with a user API key on all plans. "
            "Team Admin / Organization / Analytics / Bugbot / AI Code Tracking "
            "tools require Enterprise keys with the appropriate scopes. "
            "Fleet (private-workers) tools need the pool service-account key. "
            "Automations use Cursor's Connect API with a user key or session token. "
            "Get an existing automation by UUID; updates support metadata and one prompt. " + writes
        ),
    )
    register_read_tools(mcp)
    register_fleet_tools(mcp)
    register_org_read_tools(mcp)
    register_analytics_tools(mcp)
    register_ai_code_tools(mcp)
    register_bugbot_read_tools(mcp)
    register_automation_read_tools(mcp)
    if not config.read_only:
        register_write_tools(mcp)
        register_org_write_tools(mcp)
        register_bugbot_write_tools(mcp)
    if not config.read_only or config.allow_automation_writes:
        register_automation_write_tools(mcp)
    return mcp


def main(argv: list[str] | None = None) -> None:
    """Parse flags and run the MCP server over stdio."""
    parser = argparse.ArgumentParser(
        prog="cursor-api-mcp",
        description="MCP server for Cursor HTTP APIs (Cloud Agents + Admin + Automations).",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help=(
            "Expose only read/query tools unless --allow-automation-writes is enabled. "
            "Also enabled when CURSOR_API_READ_ONLY is 1/true/yes/on."
        ),
    )
    parser.add_argument(
        "--allow-automation-writes",
        action="store_true",
        help=(
            "Allow update_automation even in read-only mode. Also enabled when "
            "CURSOR_API_ALLOW_AUTOMATION_WRITES is 1/true/yes/on."
        ),
    )
    args = parser.parse_args(argv)
    config = ServerConfig.from_env(
        read_only_flag=args.read_only,
        allow_automation_writes_flag=args.allow_automation_writes,
    )
    build_server(config).run()


if __name__ == "__main__":
    main()
