"""Tests for URL path-segment guards."""

from __future__ import annotations

import pytest

from cursor_api_mcp.path_safety import assert_safe_api_path, require_path_segment


def test_require_path_segment_accepts_normal_ids() -> None:
    assert require_path_segment("pw_abc", field_name="worker_id") == "pw_abc"
    assert (
        require_path_segment(
            "abc123,def456",
            field_name="commit_hash",
            allow_comma_separated=True,
        )
        == "abc123,def456"
    )


@pytest.mark.parametrize(
    "value",
    [
        "../teams/members",
        "..",
        ".",
        "a/b",
        "a\\b",
        "x%2e%2e",
        "x%2Fteams",
        "",
        "  ",
    ],
)
def test_require_path_segment_rejects_traversal(value: str) -> None:
    with pytest.raises(ValueError, match="non-empty|path segment"):
        require_path_segment(value, field_name="worker_id")


def test_assert_safe_api_path_rejects_dotdot_segments() -> None:
    with pytest.raises(ValueError, match="\\.\\."):
        assert_safe_api_path("/organizations/groups/../../../teams/members")
