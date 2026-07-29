"""Organization Admin API tools (Enterprise Organization API keys)."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from cursor_api_mcp.path_safety import require_path_segment
from cursor_api_mcp.tools._common import client, error_payload, parse_json_list


def register_org_read_tools(mcp: MCPServer) -> None:
    """Register organization read/query tools."""

    def get_organization_pooled_usage(organization_id: str) -> dict[str, Any]:
        """Get org pooled usage (POST /organizations/pooled-usage; query only).

        Requires Organization API key with usage:* (or admin:*).

        Args:
            organization_id: Public org id (org_...).
        """
        try:
            return client().post_json(
                "/organizations/pooled-usage",
                body={"organizationId": organization_id},
            )
        except Exception as exc:
            return error_payload(exc)

    def get_organization_usage_events(
        organization_id: str,
        start_date_ms: int | None = None,
        end_date_ms: int | None = None,
        team_ids_json: str | list[Any] | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Get org-wide usage events (POST /organizations/filtered-usage-events).

        Args:
            organization_id: Public org id (org_...).
            start_date_ms: Optional range start as epoch milliseconds.
            end_date_ms: Optional range end as epoch milliseconds.
            team_ids_json: Optional JSON array of team ids to include.
            page: 1-indexed page (default 1).
            page_size: Page size (default 100).
        """
        body: dict[str, Any] = {
            "organizationId": organization_id,
            "page": page,
            "pageSize": page_size,
        }
        if start_date_ms is not None:
            body["startDate"] = start_date_ms
        if end_date_ms is not None:
            body["endDate"] = end_date_ms
        try:
            team_ids = parse_json_list(team_ids_json, field_name="team_ids_json")
            if team_ids is not None:
                body["teamIds"] = team_ids
            return client().post_json("/organizations/filtered-usage-events", body=body)
        except Exception as exc:
            return error_payload(exc)

    def get_organization_daily_usage_data(
        organization_id: str,
        start_date_ms: int,
        end_date_ms: int,
        team_ids_json: str | list[Any] | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Get org daily usage (POST /organizations/daily-usage-data).

        Args:
            organization_id: Public org id (org_...).
            start_date_ms: Range start as epoch milliseconds.
            end_date_ms: Range end as epoch milliseconds.
            team_ids_json: Optional JSON array of team ids.
            page: Optional page (use with page_size).
            page_size: Optional page size (use with page).
        """
        if (page is None) != (page_size is None):
            return {
                "error": True,
                "message": "page and page_size must both be set, or both omitted",
            }
        body: dict[str, Any] = {
            "organizationId": organization_id,
            "startDate": start_date_ms,
            "endDate": end_date_ms,
        }
        if page is not None:
            body["page"] = page
            body["pageSize"] = page_size
        try:
            team_ids = parse_json_list(team_ids_json, field_name="team_ids_json")
            if team_ids is not None:
                body["teamIds"] = team_ids
            return client().post_json("/organizations/daily-usage-data", body=body)
        except Exception as exc:
            return error_payload(exc)

    def get_organization_spending_data(
        organization_id: str,
        search_term: str | None = None,
        page: int = 1,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Get org spend (POST /organizations/spend).

        Args:
            organization_id: Public org id (org_...).
            search_term: Optional name/email filter.
            page: 1-indexed page (default 1).
            page_size: Optional page size.
        """
        body: dict[str, Any] = {"organizationId": organization_id, "page": page}
        if search_term is not None:
            body["searchTerm"] = search_term
        if page_size is not None:
            body["pageSize"] = page_size
        try:
            return client().post_json("/organizations/spend", body=body)
        except Exception as exc:
            return error_payload(exc)

    def list_organization_groups(
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List organization groups (GET /organizations/groups).

        Args:
            page: 1-indexed page (default 1).
            page_size: Groups per page (default 50).
        """
        try:
            return client().get(
                "/organizations/groups",
                params={"page": page, "pageSize": page_size},
            )
        except Exception as exc:
            return error_payload(exc)

    def get_organization_group(group_id: str) -> dict[str, Any]:
        """Get one organization group (GET /organizations/groups/{groupId}).

        Args:
            group_id: Organization group id (g_...).
        """
        try:
            safe_id = require_path_segment(group_id, field_name="group_id")
            return client().get(f"/organizations/groups/{safe_id}")
        except Exception as exc:
            return error_payload(exc)

    def list_organization_group_members(
        group_id: str,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        """List members of an organization group (GET .../groups/{id}/members).

        Args:
            group_id: Organization group id (g_...).
            page: 1-indexed page (default 1).
            page_size: Members per page (default 50).
        """
        try:
            safe_id = require_path_segment(group_id, field_name="group_id")
            return client().get(
                f"/organizations/groups/{safe_id}/members",
                params={"page": page, "pageSize": page_size},
            )
        except Exception as exc:
            return error_payload(exc)

    for fn in (
        get_organization_pooled_usage,
        get_organization_usage_events,
        get_organization_daily_usage_data,
        get_organization_spending_data,
        list_organization_groups,
        get_organization_group,
        list_organization_group_members,
    ):
        mcp.add_tool(fn)


def register_org_write_tools(mcp: MCPServer) -> None:
    """Register organization mutating tools."""

    def add_organization_group_members(
        group_id: str,
        user_ids_json: str | list[Any],
    ) -> dict[str, Any]:
        """Add members to an org group (POST .../members/bulk-add).

        Args:
            group_id: Organization group id (g_...).
            user_ids_json: JSON array of user ids (max 100 per request).
        """
        try:
            safe_id = require_path_segment(group_id, field_name="group_id")
            user_ids = parse_json_list(user_ids_json, field_name="user_ids_json")
            if not user_ids:
                return {"error": True, "message": "user_ids_json must be a non-empty array"}
            return client().post_json(
                f"/organizations/groups/{safe_id}/members/bulk-add",
                body={"userIds": user_ids},
            )
        except Exception as exc:
            return error_payload(exc)

    def remove_organization_group_members(
        group_id: str,
        user_ids_json: str | list[Any],
    ) -> dict[str, Any]:
        """Remove members from an org group (POST .../members/bulk-remove).

        Args:
            group_id: Organization group id (g_...).
            user_ids_json: JSON array of user ids (max 100 per request).
        """
        try:
            safe_id = require_path_segment(group_id, field_name="group_id")
            user_ids = parse_json_list(user_ids_json, field_name="user_ids_json")
            if not user_ids:
                return {"error": True, "message": "user_ids_json must be a non-empty array"}
            return client().post_json(
                f"/organizations/groups/{safe_id}/members/bulk-remove",
                body={"userIds": user_ids},
            )
        except Exception as exc:
            return error_payload(exc)

    for fn in (add_organization_group_members, remove_organization_group_members):
        mcp.add_tool(fn)
