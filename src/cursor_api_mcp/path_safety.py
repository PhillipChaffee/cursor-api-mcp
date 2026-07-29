"""Guards against URL path traversal when building Cursor API paths."""

from __future__ import annotations


def require_path_segment(
    value: str,
    *,
    field_name: str,
    allow_comma_separated: bool = False,
) -> str:
    """Return ``value`` if it is safe to interpolate into a URL path segment.

    Rejects empty values, ``.`` / ``..``, raw or encoded separators, and other
    characters that would let httpx normalize the request onto another path.

    Args:
        value: Candidate path segment (or comma-separated segments).
        field_name: Parameter name used in error messages.
        allow_comma_separated: When True, each comma-separated piece is checked.

    Returns:
        The original ``value`` unchanged when valid.

    Raises:
        ValueError: If ``value`` is not a safe path segment.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    parts = value.split(",") if allow_comma_separated else [value]
    for raw_part in parts:
        segment = raw_part.strip() if allow_comma_separated else raw_part
        if not segment:
            raise ValueError(f"{field_name} must not contain empty segments")
        lowered = segment.lower()
        if (
            segment in {".", ".."}
            or "/" in segment
            or "\\" in segment
            or "?" in segment
            or "#" in segment
            or "%2f" in lowered
            or "%5c" in lowered
            or "%2e" in lowered
        ):
            raise ValueError(
                f"{field_name} must be a single URL path segment "
                "(no '/', '\\\\', '.', '..', or encoded separators)"
            )
    return value


def assert_safe_api_path(path: str) -> None:
    """Reject API paths that contain traversal segments or encoded separators.

    Args:
        path: Absolute API path beginning with ``/``.

    Raises:
        ValueError: If the path could be normalized onto another route.
    """
    lowered = path.lower()
    if "\\" in path or "%2f" in lowered or "%5c" in lowered or "%2e" in lowered:
        raise ValueError("API path must not contain encoded separators or backslashes")
    for segment in path.split("/"):
        if segment in {".", ".."}:
            raise ValueError("API path must not contain '.' or '..' segments")
