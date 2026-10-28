from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import UUID

from mcp.server.mcpserver import MCPServer
from pydantic import StrictInt

from cursor_api_mcp.automations import AutomationsClient
from cursor_api_mcp.tools._common import error_payload


def _get_body(automation_id: str, team_id: int | None) -> dict[str, Any]:
    try:
        normalized_id = str(UUID(automation_id))
    except ValueError:
        raise ValueError("automation_id must be a UUID") from None
    body: dict[str, Any] = {"automationId": normalized_id}
    if team_id is not None:
        if not 1 <= team_id <= 2**31 - 1:
            raise ValueError("team_id must be a positive int32")
        body["teamId"] = team_id
    return body


def _editable_workflow(payload: dict[str, Any], automation_id: str) -> dict[str, Any]:
    if "restrictedSummary" in payload:
        raise ValueError("Restricted automation access cannot supply a workflow for editing")
    owner = payload.get("workflow")
    automation = owner.get("workflow") if isinstance(owner, dict) else None
    if not isinstance(automation, dict) or automation.get("automationId") != automation_id:
        raise ValueError("Automation response must contain the full matching automation")
    workflow = automation.get("workflow")
    if not isinstance(workflow, dict):
        raise ValueError("Automation response is missing its full workflow")
    for field in ("triggers", "actions", "prompts"):
        items = workflow.get(field, [])
        if not isinstance(items, list) or any(not isinstance(item, dict) for item in items):
            raise ValueError("Automation workflow has malformed triggers, actions, or prompts")
    prompts = workflow.get("prompts", [])
    if not prompts or any(not isinstance(item.get("prompt", ""), str) for item in prompts):
        raise ValueError("Automation workflow must contain valid prompts to edit")
    return workflow


def register_automation_read_tools(mcp: MCPServer) -> None:
    def get_automation(automation_id: str, team_id: StrictInt | None = None) -> dict[str, Any]:
        """Get an existing automation by UUID using Cursor's Connect API.

        Returns the full authorized response, including prompts, triggers, actions,
        ownership, and MCP auth states. A restrictedSummary means limited access.
        Obtain the UUID from the existing automation's Cursor URL or Terraform state.
        This server does not list automations.

        Args:
            automation_id: Existing automation UUID.
            team_id: Optional positive int32 team ID for read authorization.
        """
        try:
            body = _get_body(automation_id, team_id)
            return AutomationsClient().call("GetAutomation", body)
        except Exception as exc:
            return error_payload(exc)

    mcp.add_tool(get_automation)


def register_automation_write_tools(mcp: MCPServer) -> None:
    def update_automation(
        automation_id: str,
        name: str | None = None,
        description: str | None = None,
        enabled: bool | None = None,
        prompt: str | None = None,
        prompt_index: StrictInt | None = None,
        team_id: StrictInt | None = None,
    ) -> dict[str, Any]:
        """Update selected metadata or one prompt of an existing automation.

        Obtain the UUID from the existing automation's Cursor URL or Terraform state.
        Omitted metadata stays unchanged. False and empty strings are explicit edits.
        A prompt edit fetches a fresh full workflow, changes only that prompt's text,
        and sends a complete workflow replacement preserving all other fields.
        There is no compare-and-swap protection. Concurrent edits can be overwritten.
        Writes are never retried automatically. Inspect state before retrying a failure.

        Args:
            automation_id: Existing automation UUID.
            name: Replacement name, including an empty string.
            description: Replacement description, including an empty string.
            enabled: Enable or disable the automation.
            prompt: Replacement prompt text, including an empty string.
            prompt_index: Zero-based index. Required for multiple prompts. Needs prompt.
            team_id: Optional positive int32 team ID for the prompt edit's read only.
        """
        try:
            read_body = _get_body(automation_id, team_id)
            if prompt_index is not None and (prompt is None or prompt_index < 0):
                raise ValueError("prompt_index must be nonnegative and requires prompt")
            body: dict[str, Any] = {
                key: value
                for key, value in {
                    "name": name,
                    "description": description,
                    "enabled": enabled,
                }.items()
                if value is not None
            }
            if not body and prompt is None:
                raise ValueError("Provide at least one metadata or prompt edit")
            body["automationId"] = read_body["automationId"]
            client = AutomationsClient()
            if prompt is not None:
                response = client.call("GetAutomation", read_body)
                workflow = _editable_workflow(response, read_body["automationId"])
                if prompt_index is None and len(workflow["prompts"]) != 1:
                    raise ValueError("prompt_index is required for a multi-prompt automation")
                index = 0 if prompt_index is None else prompt_index
                if index >= len(workflow["prompts"]):
                    raise ValueError("prompt_index is outside the automation's prompts")
                body["workflow"] = deepcopy(workflow)
                body["workflow"]["prompts"][index]["prompt"] = prompt
            return client.call("UpdateAutomation", body)
        except Exception as exc:
            return error_payload(exc)

    mcp.add_tool(update_automation)
