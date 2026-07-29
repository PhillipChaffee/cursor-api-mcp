"""Write tools for Cursor Cloud Agents, Admin, and Organization APIs."""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from cursor_api_mcp.tools._common import (
    client,
    error_payload,
    parse_json_list,
    parse_json_object,
)

# Re-export under previous private names for existing tests/imports.
_parse_json_list = parse_json_list
_parse_json_object = parse_json_object

_CREATE_AGENT_RESERVED_EXTRA_KEYS = frozenset(
    {
        "prompt",
        "model",
        "repos",
        "name",
        "mcpServers",
        "autoCreatePR",
        "workOnCurrentBranch",
        "mode",
        "agentId",
    }
)


def _redact_worker_token_response(payload: Any) -> Any:
    """Return worker-token API payload without exposing accessToken to MCP clients."""
    if not isinstance(payload, dict) or "accessToken" not in payload:
        return payload
    redacted = dict(payload)
    redacted["accessToken"] = "[redacted]"
    redacted["accessTokenRedacted"] = True
    return redacted


def register_write_tools(mcp: MCPServer) -> None:
    """Register mutating tools on ``mcp`` (omitted in read-only mode)."""

    def create_agent(
        prompt_text: str,
        name: str | None = None,
        repo_url: str | None = None,
        starting_ref: str | None = None,
        pr_url: str | None = None,
        model_id: str | None = None,
        auto_create_pr: bool | None = None,
        work_on_current_branch: bool = False,
        mode: str | None = None,
        agent_id: str | None = None,
        prompt_images_json: str | list[Any] | None = None,
        mcp_servers_json: str | list[Any] | None = None,
        extra_json: str | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a Cloud Agent and enqueue its initial run (POST /v1/agents).

        Args:
            prompt_text: Required instruction text for the agent.
            name: Optional display name (max 100 chars).
            repo_url: Optional GitHub repository URL.
            starting_ref: Optional branch or SHA starting point.
            pr_url: Optional PR URL (repo_url still required when set).
            model_id: Optional model id from list_models.
            auto_create_pr: Whether to open a PR when the run completes.
            work_on_current_branch: Push to starting ref instead of a new branch.
            mode: Initial mode: agent or plan.
            agent_id: Optional client-supplied id (bc-...) for idempotent create.
            prompt_images_json: Optional JSON array of prompt images ({data,mimeType}
                or {url}).
            mcp_servers_json: Optional JSON array (string or list) of inline MCP servers.
            extra_json: Optional JSON object (string or object) merged into the
                request body for advanced fields. Cannot overwrite keys already set
                by typed args (for model.params, omit model_id and pass full model).
        """
        if (pr_url is not None or starting_ref is not None) and repo_url is None:
            return {
                "error": True,
                "message": "repo_url is required when pr_url or starting_ref is set",
            }
        prompt: dict[str, Any] = {"text": prompt_text}
        try:
            images = _parse_json_list(prompt_images_json, field_name="prompt_images_json")
            if images is not None:
                prompt["images"] = images
        except Exception as exc:
            return error_payload(exc)
        body: dict[str, Any] = {"prompt": prompt}
        if name is not None:
            body["name"] = name
        if model_id is not None:
            body["model"] = {"id": model_id}
        if repo_url is not None:
            repo: dict[str, Any] = {"url": repo_url}
            if starting_ref is not None:
                repo["startingRef"] = starting_ref
            if pr_url is not None:
                repo["prUrl"] = pr_url
            body["repos"] = [repo]
        if auto_create_pr is not None:
            body["autoCreatePR"] = auto_create_pr
        if work_on_current_branch:
            body["workOnCurrentBranch"] = True
        if mode is not None:
            body["mode"] = mode
        if agent_id is not None:
            body["agentId"] = agent_id
        try:
            mcp_servers = _parse_json_list(mcp_servers_json, field_name="mcp_servers_json")
            if mcp_servers is not None:
                body["mcpServers"] = mcp_servers
            extra = _parse_json_object(extra_json, field_name="extra_json")
            if extra:
                conflicts = sorted(
                    key
                    for key in _CREATE_AGENT_RESERVED_EXTRA_KEYS.intersection(extra)
                    if key in body
                )
                if conflicts:
                    return {
                        "error": True,
                        "message": (
                            "extra_json cannot overwrite keys already set by typed "
                            f"arguments: {conflicts}"
                        ),
                    }
                body.update(extra)
            return client().post_json("/v1/agents", body=body)
        except Exception as exc:
            return error_payload(exc)

    def create_agent_run(
        agent_id: str,
        prompt_text: str,
        mode: str | None = None,
        prompt_images_json: str | list[Any] | None = None,
        mcp_servers_json: str | list[Any] | None = None,
        extra_json: str | dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a follow-up prompt to an active agent (POST /v1/agents/{id}/runs).

        Args:
            agent_id: Agent id (for example bc-...).
            prompt_text: Follow-up instruction text.
            mode: Optional mode override: agent or plan.
            prompt_images_json: Optional JSON array of prompt images.
            mcp_servers_json: Optional JSON array of MCP servers for this run.
            extra_json: Optional JSON object merged into the body. Cannot overwrite
                prompt, mcpServers, or mode when those were set by typed args.
        """
        prompt: dict[str, Any] = {"text": prompt_text}
        body: dict[str, Any] = {"prompt": prompt}
        if mode is not None:
            body["mode"] = mode
        try:
            images = _parse_json_list(prompt_images_json, field_name="prompt_images_json")
            if images is not None:
                prompt["images"] = images
            mcp_servers = _parse_json_list(mcp_servers_json, field_name="mcp_servers_json")
            if mcp_servers is not None:
                body["mcpServers"] = mcp_servers
            extra = _parse_json_object(extra_json, field_name="extra_json")
            if extra:
                conflicts = sorted(
                    key for key in {"prompt", "mcpServers", "mode"}.intersection(extra) if key in body
                )
                if conflicts:
                    return {
                        "error": True,
                        "message": (
                            "extra_json cannot overwrite keys already set by typed "
                            f"arguments: {conflicts}"
                        ),
                    }
                body.update(extra)
            return client().post_json(f"/v1/agents/{agent_id}/runs", body=body)
        except Exception as exc:
            return error_payload(exc)

    def cancel_agent_run(agent_id: str, run_id: str) -> dict[str, Any]:
        """Cancel an active agent run (POST .../runs/{runId}/cancel).

        Args:
            agent_id: Agent id (for example bc-...).
            run_id: Run id (for example run-...).
        """
        try:
            return client().post_json(f"/v1/agents/{agent_id}/runs/{run_id}/cancel")
        except Exception as exc:
            return error_payload(exc)

    def archive_agent(agent_id: str) -> dict[str, Any]:
        """Archive an agent so it cannot accept new runs (POST .../archive).

        Args:
            agent_id: Agent id (for example bc-...).
        """
        try:
            return client().post_json(f"/v1/agents/{agent_id}/archive")
        except Exception as exc:
            return error_payload(exc)

    def unarchive_agent(agent_id: str) -> dict[str, Any]:
        """Unarchive an agent so it can accept new runs (POST .../unarchive).

        Args:
            agent_id: Agent id (for example bc-...).
        """
        try:
            return client().post_json(f"/v1/agents/{agent_id}/unarchive")
        except Exception as exc:
            return error_payload(exc)

    def delete_agent(agent_id: str) -> dict[str, Any]:
        """Permanently delete an agent (DELETE /v1/agents/{id}). Irreversible.

        Args:
            agent_id: Agent id (for example bc-...).
        """
        try:
            return client().delete(f"/v1/agents/{agent_id}")
        except Exception as exc:
            return error_payload(exc)

    def create_worker_token(
        for_user_email: str | None = None,
        for_user_id: int | None = None,
    ) -> dict[str, Any]:
        """Mint a one-hour user-scoped worker token (POST /v1/sub-tokens).

        Requires a service-account API key. Provide exactly one of email or user id.
        The accessToken value is redacted in the tool result.

        Args:
            for_user_email: Active team member email.
            for_user_id: Active team member numeric user id.
        """
        if (for_user_email is None) == (for_user_id is None):
            return {
                "error": True,
                "message": "Provide exactly one of for_user_email or for_user_id",
            }
        body: dict[str, Any] = {}
        if for_user_email is not None:
            body["forUserEmail"] = for_user_email
        if for_user_id is not None:
            body["forUserId"] = for_user_id
        try:
            return _redact_worker_token_response(
                client().post_json("/v1/sub-tokens", body=body)
            )
        except Exception as exc:
            return error_payload(exc)

    def set_user_spend_limit(
        user_email: str,
        spend_limit_dollars: int | None,
    ) -> dict[str, Any]:
        """Set or clear a user's spend limit (POST /teams/user-spend-limit).

        Args:
            user_email: Team member email.
            spend_limit_dollars: Integer dollar limit, or null to clear.
        """
        try:
            return client().post_json(
                "/teams/user-spend-limit",
                body={
                    "userEmail": user_email,
                    "spendLimitDollars": spend_limit_dollars,
                },
            )
        except Exception as exc:
            return error_payload(exc)

    def remove_team_member(
        user_id: str | None = None,
        email: str | None = None,
    ) -> dict[str, Any]:
        """Remove a member from the team (POST /teams/remove-member).

        Provide exactly one of user_id or email.

        Args:
            user_id: Encoded user id (user_...).
            email: Team member email.
        """
        if (user_id is None) == (email is None):
            return {
                "error": True,
                "message": "Provide exactly one of user_id or email",
            }
        body: dict[str, Any] = {}
        if user_id is not None:
            body["userId"] = user_id
        if email is not None:
            body["email"] = email
        try:
            return client().post_json("/teams/remove-member", body=body)
        except Exception as exc:
            return error_payload(exc)

    def upsert_repo_blocklists(repos_json: str | list[Any]) -> dict[str, Any]:
        """Upsert repository blocklist patterns (POST .../repos/upsert).

        Args:
            repos_json: JSON array of {url, patterns[]} objects.
        """
        try:
            repos = _parse_json_list(repos_json, field_name="repos_json")
            if not repos:
                return {"error": True, "message": "repos_json must be a non-empty array"}
            return client().post_json(
                "/settings/repo-blocklists/repos/upsert",
                body={"repos": repos},
            )
        except Exception as exc:
            return error_payload(exc)

    def delete_repo_blocklist(repo_id: str) -> dict[str, Any]:
        """Delete one repository blocklist entry (DELETE .../repos/{repoId}).

        Args:
            repo_id: Blocklist repo id.
        """
        try:
            return client().delete(f"/settings/repo-blocklists/repos/{repo_id}")
        except Exception as exc:
            return error_payload(exc)

    def create_billing_group(name: str, group_type: str = "BILLING") -> dict[str, Any]:
        """Create a billing group (POST /teams/groups).

        Args:
            name: Group name.
            group_type: Group type (currently only BILLING).
        """
        try:
            return client().post_json(
                "/teams/groups",
                body={"name": name, "type": group_type},
            )
        except Exception as exc:
            return error_payload(exc)

    def update_billing_group(
        group_id: str,
        name: str | None = None,
        directory_group_id: str | None = None,
        clear_directory_group: bool = False,
    ) -> dict[str, Any]:
        """Update a billing group name or directory attachment (PATCH /teams/groups/{id}).

        Only one field can be updated per request per API rules.

        Args:
            group_id: Billing group id.
            name: New group name.
            directory_group_id: Directory group id to attach.
            clear_directory_group: When True, detach directory sync (sends null).
        """
        body: dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        elif clear_directory_group:
            body["directoryGroupId"] = None
        elif directory_group_id is not None:
            body["directoryGroupId"] = directory_group_id
        else:
            return {
                "error": True,
                "message": (
                    "Provide name, directory_group_id, or clear_directory_group=true"
                ),
            }
        try:
            return client().patch_json(f"/teams/groups/{group_id}", body=body)
        except Exception as exc:
            return error_payload(exc)

    def delete_billing_group(group_id: str) -> dict[str, Any]:
        """Delete a billing group (DELETE /teams/groups/{id}). Destructive.

        Args:
            group_id: Billing group id.
        """
        try:
            return client().delete(f"/teams/groups/{group_id}")
        except Exception as exc:
            return error_payload(exc)

    def add_billing_group_members(
        group_id: str,
        user_ids_json: str | list[Any],
    ) -> dict[str, Any]:
        """Add members to a billing group (POST /teams/groups/{id}/members).

        Args:
            group_id: Billing group id.
            user_ids_json: JSON array of encoded user ids.
        """
        try:
            user_ids = _parse_json_list(user_ids_json, field_name="user_ids_json")
            if not user_ids:
                return {"error": True, "message": "user_ids_json must be a non-empty array"}
            return client().post_json(
                f"/teams/groups/{group_id}/members",
                body={"userIds": user_ids},
            )
        except Exception as exc:
            return error_payload(exc)

    def remove_billing_group_members(
        group_id: str,
        user_ids_json: str | list[Any],
    ) -> dict[str, Any]:
        """Remove members from a billing group (DELETE /teams/groups/{id}/members).

        Args:
            group_id: Billing group id.
            user_ids_json: JSON array of encoded user ids.
        """
        try:
            user_ids = _parse_json_list(user_ids_json, field_name="user_ids_json")
            if not user_ids:
                return {"error": True, "message": "user_ids_json must be a non-empty array"}
            return client().delete(
                f"/teams/groups/{group_id}/members",
                body={"userIds": user_ids},
            )
        except Exception as exc:
            return error_payload(exc)

    def sync_organization_team_memberships(
        organization_id: str,
        users_json: str | list[Any],
    ) -> dict[str, Any]:
        """Sync org users onto linked teams (POST /organizations/team-memberships/sync).

        Requires Organization API key with members:* (or admin:*).

        Args:
            organization_id: Public org id (org_...).
            users_json: JSON array of {userId, teamIds[]} or
                {userId, destinationTeamId} entries.
        """
        try:
            users = _parse_json_list(users_json, field_name="users_json")
            if not users:
                return {"error": True, "message": "users_json must be a non-empty array"}
            return client().post_json(
                "/organizations/team-memberships/sync",
                body={"organizationId": organization_id, "users": users},
            )
        except Exception as exc:
            return error_payload(exc)

    for fn in (
        create_agent,
        create_agent_run,
        cancel_agent_run,
        archive_agent,
        unarchive_agent,
        delete_agent,
        create_worker_token,
        set_user_spend_limit,
        remove_team_member,
        upsert_repo_blocklists,
        delete_repo_blocklist,
        create_billing_group,
        update_billing_group,
        delete_billing_group,
        add_billing_group_members,
        remove_billing_group_members,
        sync_organization_team_memberships,
    ):
        mcp.add_tool(fn)
