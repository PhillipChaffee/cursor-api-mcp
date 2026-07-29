"""Bugbot API tools (Enterprise)."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from cursor_api_mcp.tools._common import client, error_payload


def register_bugbot_read_tools(mcp: MCPServer) -> None:
    """Register Bugbot read tools."""

    def list_bugbot_repos() -> dict[str, Any]:
        """List repos with Bugbot settings (GET /bugbot/repos)."""
        try:
            return client().get("/bugbot/repos")
        except Exception as exc:
            return error_payload(exc)

    mcp.add_tool(list_bugbot_repos)


def register_bugbot_write_tools(mcp: MCPServer) -> None:
    """Register Bugbot mutating tools."""

    def trigger_bugbot_review(pr_url: str, dry_run: bool = False) -> dict[str, Any]:
        """Queue a Bugbot review (POST /bugbot/review).

        Args:
            pr_url: Full GitHub PR or GitLab MR URL.
            dry_run: When True, analyze without posting to SCM (still billed).
        """
        body: dict[str, Any] = {"prUrl": pr_url}
        if dry_run:
            body["dryRun"] = True
        try:
            return client().post_json("/bugbot/review", body=body)
        except Exception as exc:
            return error_payload(exc)

    def update_bugbot_repo(
        repo_url: str,
        enabled: bool,
        manual_trigger_only: bool | None = None,
    ) -> dict[str, Any]:
        """Enable/disable Bugbot for a repo (POST /bugbot/repo/update).

        Args:
            repo_url: Full repository URL.
            enabled: True to enable Bugbot, False to disable.
            manual_trigger_only: When True, skip automatic PR reviews.
        """
        body: dict[str, Any] = {"repoUrl": repo_url, "enabled": enabled}
        if manual_trigger_only is not None:
            body["manualTriggerOnly"] = manual_trigger_only
        try:
            return client().post_json("/bugbot/repo/update", body=body)
        except Exception as exc:
            return error_payload(exc)

    def update_bugbot_user_access(username: str, allow: bool) -> dict[str, Any]:
        """Update Bugbot allow/block list membership (POST /bugbot/user/update).

        Team settings must already use allowlist or blocklist mode.

        Args:
            username: GitHub/GitLab/Bitbucket username (case-insensitive).
            allow: Grant (True) or revoke (False) access per active list mode.
        """
        try:
            return client().post_json(
                "/bugbot/user/update",
                body={"username": username, "allow": allow},
            )
        except Exception as exc:
            return error_payload(exc)

    for fn in (trigger_bugbot_review, update_bugbot_repo, update_bugbot_user_access):
        mcp.add_tool(fn)
