"""Shared helpers for MCP tool implementations."""

from __future__ import annotations

import json
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


def parse_json_object(
    raw: str | dict[str, Any] | None,
    *,
    field_name: str,
) -> dict[str, Any] | None:
    """Parse a JSON object from a string, or accept an already-decoded mapping."""
    if raw is None or raw == "":
        return None
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise ValueError(f"{field_name} must be a JSON object string or object")
    if raw.strip() == "":
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def parse_json_list(
    raw: str | list[Any] | None,
    *,
    field_name: str,
) -> list[Any] | None:
    """Parse a JSON array from a string, or accept an already-decoded list."""
    if raw is None or raw == "":
        return None
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, str):
        raise ValueError(f"{field_name} must be a JSON array string or array")
    if raw.strip() == "":
        return None
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field_name} must be valid JSON: {exc}") from exc
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return value
