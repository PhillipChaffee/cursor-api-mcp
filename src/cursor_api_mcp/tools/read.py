"""Read tools for Cursor Cloud Agents, Admin, and Organization APIs."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from cursor_api_mcp.tools._common import client, error_payload


def register_read_tools(mcp: MCPServer) -> None:
    """Register all read / query tools on ``mcp``."""

    def get_api_key_info() -> dict[str, Any]:
        """Return metadata for the configured Cursor API key (GET /v1/me)."""
        try:
            return client().get("/v1/me")
        except Exception as exc:
            return error_payload(exc)

    def list_models() -> dict[str, Any]:
        """List models available for Cloud Agents (GET /v1/models)."""
        try:
            return client().get("/v1/models")
        except Exception as exc:
            return error_payload(exc)

    def list_repositories() -> dict[str, Any]:
        """List GitHub repos accessible via Cursor's GitHub App (GET /v1/repositories).

        Strict rate limits: about 1 request/user/minute and 30/user/hour. Can be slow.
        """
        try:
            return client().get("/v1/repositories")
        except Exception as exc:
            return error_payload(exc)

    def list_agents(
        limit: int = 20,
        cursor: str | None = None,
        pr_url: str | None = None,
        include_archived: bool = True,
    ) -> dict[str, Any]:
        """List Cloud Agents for the authenticated user (GET /v1/agents).

        Args:
            limit: Page size (1-100, default 20).
            cursor: Pagination cursor from a previous nextCursor.
            pr_url: Optional GitHub pull request URL filter.
            include_archived: Include archived agents (default True).
        """
        try:
            return client().get(
                "/v1/agents",
                params={
                    "limit": min(max(limit, 1), 100),
                    "cursor": cursor,
                    "prUrl": pr_url,
                    "includeArchived": str(include_archived).lower(),
                },
            )
        except Exception as exc:
            return error_payload(exc)

    def get_agent(agent_id: str) -> dict[str, Any]:
        """Get durable metadata for one Cloud Agent (GET /v1/agents/{id}).

        Args:
            agent_id: Agent id (for example bc-...).
        """
        try:
            return client().get(f"/v1/agents/{agent_id}")
        except Exception as exc:
            return error_payload(exc)

    def list_agent_runs(
        agent_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """List runs for a Cloud Agent, newest first (GET /v1/agents/{id}/runs).

        Args:
            agent_id: Agent id (for example bc-...).
            limit: Page size (1-100, default 20).
            cursor: Pagination cursor from a previous nextCursor.
        """
        try:
            return client().get(
                f"/v1/agents/{agent_id}/runs",
                params={"limit": min(max(limit, 1), 100), "cursor": cursor},
            )
        except Exception as exc:
            return error_payload(exc)

    def get_agent_run(agent_id: str, run_id: str) -> dict[str, Any]:
        """Get one Cloud Agent run (GET /v1/agents/{id}/runs/{runId}).

        Args:
            agent_id: Agent id (for example bc-...).
            run_id: Run id (for example run-...).
        """
        try:
            return client().get(f"/v1/agents/{agent_id}/runs/{run_id}")
        except Exception as exc:
            return error_payload(exc)

    def get_agent_usage(agent_id: str, run_id: str | None = None) -> dict[str, Any]:
        """Get token usage for an agent, optionally scoped to one run (GET .../usage).

        Args:
            agent_id: Agent id (for example bc-...).
            run_id: Optional run id to scope usage.
        """
        try:
            return client().get(
                f"/v1/agents/{agent_id}/usage",
                params={"runId": run_id},
            )
        except Exception as exc:
            return error_payload(exc)

    def list_agent_artifacts(agent_id: str) -> dict[str, Any]:
        """List artifacts produced by a Cloud Agent (GET /v1/agents/{id}/artifacts).

        Args:
            agent_id: Agent id (for example bc-...).
        """
        try:
            return client().get(f"/v1/agents/{agent_id}/artifacts")
        except Exception as exc:
            return error_payload(exc)

    def list_team_members() -> dict[str, Any]:
        """List team members (GET /teams/members). Requires a Team Admin API key."""
        try:
            return client().get("/teams/members")
        except Exception as exc:
            return error_payload(exc)

    def get_audit_logs(
        start_time: str | None = None,
        end_time: str | None = None,
        event_types: str | None = None,
        search: str | None = None,
        users: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Fetch team audit log events (GET /teams/audit-logs).

        Args:
            start_time: Start bound (e.g. 7d, ISO8601, YYYY-MM-DD). Default ~7 days ago.
            end_time: End bound (e.g. now). Default now.
            event_types: Comma-separated event types (login, add_user, ...).
            search: Free-text search filter.
            users: Comma-separated emails or encoded user ids.
            page: 1-indexed page (default 1).
            page_size: Results per page, 1-500 (default 100).
        """
        try:
            return client().get(
                "/teams/audit-logs",
                params={
                    "startTime": start_time,
                    "endTime": end_time,
                    "eventTypes": event_types,
                    "search": search,
                    "users": users,
                    "page": page,
                    "pageSize": min(max(page_size, 1), 500),
                },
            )
        except Exception as exc:
            return error_payload(exc)

    def get_daily_usage_data(
        start_date_ms: int,
        end_date_ms: int,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Fetch daily team usage metrics (POST /teams/daily-usage-data; query only).

        Date range cannot exceed 30 days. Without page/page_size, only active users
        are returned; with both, all members in range are returned.

        Args:
            start_date_ms: Range start as epoch milliseconds.
            end_date_ms: Range end as epoch milliseconds.
            page: Optional 1-indexed page for all-members mode.
            page_size: Optional page size for all-members mode.
        """
        body: dict[str, Any] = {
            "startDate": start_date_ms,
            "endDate": end_date_ms,
        }
        if page is not None:
            body["page"] = page
        if page_size is not None:
            body["pageSize"] = page_size
        try:
            return client().post_json("/teams/daily-usage-data", body=body)
        except Exception as exc:
            return error_payload(exc)

    def get_spending_data(
        search_term: str | None = None,
        sort_by: str = "date",
        sort_direction: str = "desc",
        page: int = 1,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Fetch current-cycle team spend (POST /teams/spend; query only).

        Args:
            search_term: Filter by name/email.
            sort_by: One of amount, date, user (default date).
            sort_direction: asc or desc (default desc).
            page: 1-indexed page (default 1).
            page_size: Optional page size.
        """
        body: dict[str, Any] = {
            "sortBy": sort_by,
            "sortDirection": sort_direction,
            "page": page,
        }
        if search_term is not None:
            body["searchTerm"] = search_term
        if page_size is not None:
            body["pageSize"] = page_size
        try:
            return client().post_json("/teams/spend", body=body)
        except Exception as exc:
            return error_payload(exc)

    def get_usage_events(
        start_date_ms: int | None = None,
        end_date_ms: int | None = None,
        users: str | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Fetch filtered usage events (POST /teams/filtered-usage-events; query only).

        Args:
            start_date_ms: Optional range start as epoch milliseconds.
            end_date_ms: Optional range end as epoch milliseconds.
            users: Optional comma-separated emails or user ids.
            page: 1-indexed page (default 1).
            page_size: Page size (default 100).
        """
        body: dict[str, Any] = {"page": page, "pageSize": page_size}
        if start_date_ms is not None:
            body["startDate"] = start_date_ms
        if end_date_ms is not None:
            body["endDate"] = end_date_ms
        if users is not None:
            body["users"] = users
        try:
            return client().post_json("/teams/filtered-usage-events", body=body)
        except Exception as exc:
            return error_payload(exc)

    def list_team_repo_blocklists() -> dict[str, Any]:
        """List team repository blocklists (GET /settings/repo-blocklists/repos)."""
        try:
            return client().get("/settings/repo-blocklists/repos")
        except Exception as exc:
            return error_payload(exc)

    def list_billing_groups(billing_cycle: str | None = None) -> dict[str, Any]:
        """List billing groups for the team (GET /teams/groups).

        Args:
            billing_cycle: Optional ISO date (YYYY-MM-DD) for the cycle; default current.
        """
        try:
            return client().get(
                "/teams/groups",
                params={"billingCycle": billing_cycle},
            )
        except Exception as exc:
            return error_payload(exc)

    def get_billing_group(
        group_id: str,
        billing_cycle: str | None = None,
    ) -> dict[str, Any]:
        """Get one billing group (GET /teams/groups/{groupId}).

        Args:
            group_id: Billing group id.
            billing_cycle: Optional ISO date (YYYY-MM-DD) for the cycle; default current.
        """
        try:
            return client().get(
                f"/teams/groups/{group_id}",
                params={"billingCycle": billing_cycle},
            )
        except Exception as exc:
            return error_payload(exc)

    def list_organization_members(
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List organization members (GET /organizations/members).

        Works with an Organization API key scoped to members:read (or broader).

        Args:
            page: 1-indexed page (default 1).
            page_size: Members per page, capped at 200 (default 50).
        """
        try:
            return client().get(
                "/organizations/members",
                params={"page": page, "pageSize": min(max(page_size, 1), 200)},
            )
        except Exception as exc:
            return error_payload(exc)

    for fn in (
        get_api_key_info,
        list_models,
        list_repositories,
        list_agents,
        get_agent,
        list_agent_runs,
        get_agent_run,
        get_agent_usage,
        list_agent_artifacts,
        list_team_members,
        get_audit_logs,
        get_daily_usage_data,
        get_spending_data,
        get_usage_events,
        list_team_repo_blocklists,
        list_billing_groups,
        get_billing_group,
        list_organization_members,
    ):
        mcp.add_tool(fn)
