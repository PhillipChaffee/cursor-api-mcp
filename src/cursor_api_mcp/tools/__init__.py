"""Tool registration for the Cursor API MCP server."""

from cursor_api_mcp.tools.read import register_read_tools
from cursor_api_mcp.tools.write import register_write_tools

__all__ = ["register_read_tools", "register_write_tools"]
