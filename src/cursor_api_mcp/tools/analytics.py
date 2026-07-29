"""Analytics API tools (Enterprise team admin keys)."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from cursor_api_mcp.tools._common import client, error_payload

_TEAM_METRICS = frozenset(
    {
        "agent-edits",
        "tabs",
        "dau",
        "client-versions",
        "models",
        "top-file-extensions",
        "mcp",
        "commands",
        "plans",
        "skills",
        "ask-mode",
        "conversation-insights",
        "leaderboard",
        "bugbot",
        "bugbot-reviews",
    }
)

_BY_USER_METRICS = frozenset(
    {
        "agent-edits",
        "tabs",
        "models",
        "top-file-extensions",
        "client-versions",
        "mcp",
        "commands",
        "plans",
        "skills",
        "ask-mode",
    }
)


def register_analytics_tools(mcp: MCPServer) -> None:
    """Register Analytics API read tools."""

    def get_team_analytics(
        metric: str,
        start_date: str | None = None,
        end_date: str | None = None,
        users: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        include: str | None = None,
        repo: str | None = None,
        pr_number: int | None = None,
        dry_run: bool | None = None,
    ) -> dict[str, Any]:
        """Fetch a team analytics metric (GET /analytics/team/{metric}).

        Allowed metrics: agent-edits, tabs, dau, client-versions, models,
        top-file-extensions, mcp, commands, plans, skills, ask-mode,
        conversation-insights, leaderboard, bugbot, bugbot-reviews.

        Args:
            metric: Allowlisted metric slug (see docstring list).
            start_date: Optional start (ISO, YYYY-MM-DD, 7d, today, ...).
            end_date: Optional end date bound.
            users: Optional comma-separated emails or user ids.
            page: Optional page (leaderboard / bugbot* pagination).
            page_size: Optional page size.
            include: Required for conversation-insights (comma-separated slices:
                intents,complexity,categories,guidanceLevels,workTypes).
            repo: Optional repo filter for bugbot / bugbot-reviews
                (host/owner/repo).
            pr_number: Optional PR number filter for bugbot-reviews.
            dry_run: Optional filter for bugbot-reviews (true=dry-run only).
        """
        if metric not in _TEAM_METRICS:
            return {
                "error": True,
                "message": (
                    f"Unknown team analytics metric {metric!r}. "
                    f"Allowed: {sorted(_TEAM_METRICS)}"
                ),
            }
        if metric == "conversation-insights" and not include:
            return {
                "error": True,
                "message": (
                    "include is required for conversation-insights "
                    "(e.g. intents,complexity,categories,guidanceLevels,workTypes)"
                ),
            }
        params: dict[str, Any] = {
            "startDate": start_date,
            "endDate": end_date,
            "users": users,
            "page": page,
            "pageSize": page_size,
            "include": include,
            "repo": repo,
            "prNumber": pr_number,
        }
        if dry_run is not None:
            params["dryRun"] = str(dry_run).lower()
        try:
            return client().get(f"/analytics/team/{metric}", params=params)
        except Exception as exc:
            return error_payload(exc)

    def get_analytics_by_user(
        metric: str,
        start_date: str | None = None,
        end_date: str | None = None,
        users: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Fetch a by-user analytics metric (GET /analytics/by-user/{metric}).

        Allowed metrics: agent-edits, tabs, models, top-file-extensions,
        client-versions, mcp, commands, plans, skills, ask-mode.

        Args:
            metric: Allowlisted metric slug.
            start_date: Optional start date bound.
            end_date: Optional end date bound.
            users: Optional comma-separated emails or user ids.
            page: Page number (default 1).
            page_size: Users per page (default 100, max 500 server-side).
        """
        if metric not in _BY_USER_METRICS:
            return {
                "error": True,
                "message": (
                    f"Unknown by-user analytics metric {metric!r}. "
                    f"Allowed: {sorted(_BY_USER_METRICS)}"
                ),
            }
        try:
            return client().get(
                f"/analytics/by-user/{metric}",
                params={
                    "startDate": start_date,
                    "endDate": end_date,
                    "users": users,
                    "page": page,
                    "pageSize": page_size,
                },
            )
        except Exception as exc:
            return error_payload(exc)

    for fn in (get_team_analytics, get_analytics_by_user):
        mcp.add_tool(fn)
