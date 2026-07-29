"""Cursor API MCP server entrypoint."""

from __future__ import annotations

import argparse

from mcp.server.mcpserver import MCPServer

from cursor_api_mcp.config import ServerConfig
from cursor_api_mcp.tools import (
    register_ai_code_tools,
    register_analytics_tools,
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
    mode = "read-only" if config.read_only else "read/write"
    mcp = MCPServer(
        "cursor-api",
        instructions=(
            f"Cursor HTTP API MCP ({mode}). "
            "Cloud Agents tools work with a user API key on all plans. "
            "Team Admin / Organization / Analytics / Bugbot / AI Code Tracking "
            "tools require Enterprise keys with the appropriate scopes. "
            "Fleet (private-workers) tools need the pool service-account key. "
            + (
                "Write tools are disabled in this session."
                if config.read_only
                else (
                    "Write tools can create/cancel/archive/delete agents, change "
                    "team/org settings, and mutate Bugbot config — use carefully."
                )
            )
        ),
    )
    register_read_tools(mcp)
    register_fleet_tools(mcp)
    register_org_read_tools(mcp)
    register_analytics_tools(mcp)
    register_ai_code_tools(mcp)
    register_bugbot_read_tools(mcp)
    if not config.read_only:
        register_write_tools(mcp)
        register_org_write_tools(mcp)
        register_bugbot_write_tools(mcp)
    return mcp


def main(argv: list[str] | None = None) -> None:
    """Parse flags and run the MCP server over stdio."""
    parser = argparse.ArgumentParser(
        prog="cursor-api-mcp",
        description="MCP server for Cursor HTTP APIs (Cloud Agents + Admin).",
    )
    parser.add_argument(
        "--read-only",
        action="store_true",
        help=(
            "Expose only read/query tools. Also enabled when CURSOR_API_READ_ONLY "
            "is 1/true/yes/on."
        ),
    )
    args = parser.parse_args(argv)
    config = ServerConfig.from_env(read_only_flag=args.read_only)
    build_server(config).run()


if __name__ == "__main__":
    main()
