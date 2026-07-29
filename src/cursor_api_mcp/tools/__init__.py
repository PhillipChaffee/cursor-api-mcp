"""Tool registration for the Cursor API MCP server."""

from cursor_api_mcp.tools.ai_code import register_ai_code_tools
from cursor_api_mcp.tools.analytics import register_analytics_tools
from cursor_api_mcp.tools.bugbot import (
    register_bugbot_read_tools,
    register_bugbot_write_tools,
)
from cursor_api_mcp.tools.fleet import register_fleet_tools
from cursor_api_mcp.tools.org import register_org_read_tools, register_org_write_tools
from cursor_api_mcp.tools.read import register_read_tools
from cursor_api_mcp.tools.write import register_write_tools

__all__ = [
    "register_ai_code_tools",
    "register_analytics_tools",
    "register_bugbot_read_tools",
    "register_bugbot_write_tools",
    "register_fleet_tools",
    "register_org_read_tools",
    "register_org_write_tools",
    "register_read_tools",
    "register_write_tools",
]
