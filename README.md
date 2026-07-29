# cursor-api-readonly-mcp

Read-only [MCP](https://modelcontextprotocol.io/) server for [Cursor HTTP APIs](https://cursor.com/docs/api).

It exposes **fetch-only** tools. There are no tools that create, cancel, archive,
delete, sync memberships, or change spend limits / blocklists.

## What it covers

| Area | Tools | Key type |
|------|--------|----------|
| Cloud Agents | `get_api_key_info`, `list_models`, `list_repositories`, `list_agents`, `get_agent`, `list_agent_runs`, `get_agent_run`, `get_agent_usage`, `list_agent_artifacts` | User API key (all plans) |
| Team Admin | `list_team_members`, `get_audit_logs`, `get_daily_usage_data`, `get_spending_data`, `get_usage_events`, `list_team_repo_blocklists`, `list_billing_groups`, `get_billing_group` | Team Admin key (Enterprise) |
| Organization | `list_organization_members` | Org key with `members:read`+ (Enterprise) |

Some Admin “get” endpoints use `POST` with a JSON body in Cursor’s API. Those are
still treated as read-only here (no mutations).

## Setup

1. Create an API key at [cursor.com/dashboard/api](https://cursor.com/dashboard/api).
   Prefer the narrowest scope (`members:read` for org membership reads).
2. Copy `.env.example` → `.env` and set `CURSOR_API_KEY` (optional for local runs;
   Cursor MCP config usually injects the env var instead).

```bash
cd /Users/phillipchaffee/git/cursor-api-readonly-mcp
uv sync
CURSOR_API_KEY=crsr_... uv run cursor-api-readonly-mcp
```

## Cursor MCP config

Merge into `~/.cursor/mcp.json` (do not replace existing servers):

```json
{
  "mcpServers": {
    "cursor-api-readonly": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/Users/phillipchaffee/git/cursor-api-readonly-mcp",
        "cursor-api-readonly-mcp"
      ],
      "env": {
        "CURSOR_API_KEY": "crsr_YOUR_KEY_HERE"
      }
    }
  }
}
```

Then reload MCP in Cursor Settings → MCP. Verify with a prompt like
“call get_api_key_info” or “list my cloud agents”.

## Safety model

- Tool surface: only list/get/query helpers; no write tools.
- Credentials: use a scoped key; never commit `.env` or paste keys into chat.
- Rate limits: Admin ~20/min for many routes; `/v1/repositories` is especially
  strict (~1/min). Prefer caching and avoid polling loops.

## Docs

- [Cursor APIs overview](https://cursor.com/docs/api)
- [Cloud Agents endpoints](https://cursor.com/docs/cloud-agent/api/endpoints)
- [Admin API](https://cursor.com/docs/account/teams/admin-api)
- [Organization Admin API](https://cursor.com/docs/account/organizations/organization-admin-api)
- [MCP in Cursor](https://cursor.com/docs/mcp)
