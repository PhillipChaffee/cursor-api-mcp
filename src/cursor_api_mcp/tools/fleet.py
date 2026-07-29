"""Fleet / private-worker tools for self-hosted Cloud Agent pools."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from cursor_api_mcp.tools._common import client, error_payload


def register_fleet_tools(mcp: MCPServer) -> None:
    """Register private-worker fleet read tools (service-account keys)."""

    def list_private_workers(
        status: str = "all",
        limit: int = 50,
        next_page_token: str | None = None,
    ) -> dict[str, Any]:
        """List self-hosted pool workers (GET /v0/private-workers).

        Requires the pool's service account API key.

        Args:
            status: One of all, in_use, idle (default all).
            limit: Page size 1-100 (default 50).
            next_page_token: Pagination cursor from a previous response.
        """
        try:
            return client().get(
                "/v0/private-workers",
                params={
                    "status": status,
                    "limit": min(max(limit, 1), 100),
                    "nextPageToken": next_page_token,
                },
            )
        except Exception as exc:
            return error_payload(exc)

    def get_fleet_summary() -> dict[str, Any]:
        """Get connected/in-use worker counts (GET /v0/private-workers/summary)."""
        try:
            return client().get("/v0/private-workers/summary")
        except Exception as exc:
            return error_payload(exc)

    def get_private_worker(worker_id: str) -> dict[str, Any]:
        """Get one private worker (GET /v0/private-workers/{id}).

        Args:
            worker_id: Worker id (for example pw_...).
        """
        try:
            return client().get(f"/v0/private-workers/{worker_id}")
        except Exception as exc:
            return error_payload(exc)

    def list_pending_pool_requests(
        limit: int = 50,
        page_token: str | None = None,
        repository: str | None = None,
    ) -> dict[str, Any]:
        """List unassigned pool requests (GET /v0/private-workers/pending-requests).

        Args:
            limit: Page size 1-100 (default 50).
            page_token: Pagination cursor.
            repository: Optional repo URL filter (required for repo-scoped keys).
        """
        try:
            return client().get(
                "/v0/private-workers/pending-requests",
                params={
                    "limit": min(max(limit, 1), 100),
                    "pageToken": page_token,
                    "repository": repository,
                },
            )
        except Exception as exc:
            return error_payload(exc)

    for fn in (
        list_private_workers,
        get_fleet_summary,
        get_private_worker,
        list_pending_pool_requests,
    ):
        mcp.add_tool(fn)
