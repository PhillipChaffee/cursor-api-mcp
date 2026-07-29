"""Shared helpers for MCP tool implementations."""

from __future__ import annotations

from typing import Any

from cursor_api_mcp.client import CursorApiClient, CursorApiError


def client() -> CursorApiClient:
    """Return a Cursor API client using process environment credentials."""
    return CursorApiClient()


def error_payload(exc: Exception) -> dict[str, Any]:
    """Convert an exception into a JSON-serializable tool error payload."""
    if isinstance(exc, CursorApiError):
        return {"error": True, "status_code": exc.status_code, "message": str(exc)}
    return {"error": True, "message": str(exc)}
