"""AI Code Tracking API tools (Enterprise, alpha)."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from cursor_api_mcp.path_safety import require_path_segment
from cursor_api_mcp.tools._common import client, error_payload


def register_ai_code_tools(mcp: MCPServer) -> None:
    """Register AI Code Tracking read tools."""

    def list_ai_code_commits(
        start_date: str | None = None,
        end_date: str | None = None,
        user: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """List AI commit metrics (GET /analytics/ai-code/commits).

        Args:
            start_date: Optional start (ISO, now, 7d). Default ~7 days ago.
            end_date: Optional end (ISO, now, 0d). Default now.
            user: Optional single-user filter (email, user_..., or numeric id).
            page: 1-based page (default 1).
            page_size: Results per page (default 100, max 1000).
        """
        try:
            return client().get(
                "/analytics/ai-code/commits",
                params={
                    "startDate": start_date,
                    "endDate": end_date,
                    "user": user,
                    "page": page,
                    "pageSize": min(max(page_size, 1), 1000),
                },
            )
        except Exception as exc:
            return error_payload(exc)

    def download_ai_code_commits_csv(
        start_date: str | None = None,
        end_date: str | None = None,
        user: str | None = None,
    ) -> dict[str, Any]:
        """Download AI commit metrics CSV (GET /analytics/ai-code/commits.csv).

        Returns the CSV body as text under ``csv_text``.

        Args:
            start_date: Optional start date bound.
            end_date: Optional end date bound.
            user: Optional single-user filter.
        """
        try:
            text = client().get_text(
                "/analytics/ai-code/commits.csv",
                params={
                    "startDate": start_date,
                    "endDate": end_date,
                    "user": user,
                },
                accept="text/csv",
            )
            return {"csv_text": text}
        except Exception as exc:
            return error_payload(exc)

    def list_ai_code_changes(
        start_date: str | None = None,
        end_date: str | None = None,
        user: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """List accepted AI change metrics (GET /analytics/ai-code/changes).

        Args:
            start_date: Optional start date bound.
            end_date: Optional end date bound.
            user: Optional single-user filter.
            page: 1-based page (default 1).
            page_size: Results per page (default 100, max 1000).
        """
        try:
            return client().get(
                "/analytics/ai-code/changes",
                params={
                    "startDate": start_date,
                    "endDate": end_date,
                    "user": user,
                    "page": page,
                    "pageSize": min(max(page_size, 1), 1000),
                },
            )
        except Exception as exc:
            return error_payload(exc)

    def download_ai_code_changes_csv(
        start_date: str | None = None,
        end_date: str | None = None,
        user: str | None = None,
    ) -> dict[str, Any]:
        """Download AI change metrics CSV (GET /analytics/ai-code/changes.csv).

        Returns the CSV body as text under ``csv_text``.

        Args:
            start_date: Optional start date bound.
            end_date: Optional end date bound.
            user: Optional single-user filter.
        """
        try:
            text = client().get_text(
                "/analytics/ai-code/changes.csv",
                params={
                    "startDate": start_date,
                    "endDate": end_date,
                    "user": user,
                },
                accept="text/csv",
            )
            return {"csv_text": text}
        except Exception as exc:
            return error_payload(exc)

    def get_ai_code_commit_details(
        commit_hash: str,
        branch: str | None = None,
    ) -> dict[str, Any]:
        """Get commit detail / blame (GET /analytics/ai-code/commits/{hash}).

        Limited alpha. ``commit_hash`` may be a single hash or comma-separated
        list.

        Args:
            commit_hash: Commit hash or comma-separated hashes.
            branch: Optional branch name filter.
        """
        try:
            safe_hash = require_path_segment(
                commit_hash,
                field_name="commit_hash",
                allow_comma_separated=True,
            )
            return client().get(
                f"/analytics/ai-code/commits/{safe_hash}",
                params={"branch": branch},
            )
        except Exception as exc:
            return error_payload(exc)

    for fn in (
        list_ai_code_commits,
        download_ai_code_commits_csv,
        list_ai_code_changes,
        download_ai_code_changes_csv,
        get_ai_code_commit_details,
    ):
        mcp.add_tool(fn)
