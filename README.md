# cursor-api-mcp

[MCP](https://modelcontextprotocol.io/) server for the [Cursor HTTP APIs](https://cursor.com/docs/api).

By default the server exposes **read and write** tools (Cloud Agents + Team/Org Admin).
Pass `--read-only` (or set `CURSOR_API_READ_ONLY=true`) to register only fetch/query tools.

## Install

```bash
git clone https://github.com/PhillipChaffee/cursor-api-mcp.git
cd cursor-api-mcp
uv sync
```

Create an API key at [cursor.com/dashboard/api](https://cursor.com/dashboard/api).

## Run

```bash
# Full access (read + write)
CURSOR_API_KEY=crsr_... uv run cursor-api-mcp

# Read-only (write tools are not registered)
CURSOR_API_KEY=crsr_... uv run cursor-api-mcp --read-only

# Same via env
CURSOR_API_KEY=crsr_... CURSOR_API_READ_ONLY=true uv run cursor-api-mcp
```

## Cursor MCP config

Merge into `~/.cursor/mcp.json` (do not replace existing servers).

**Read-only (recommended default):**

```json
{
  "mcpServers": {
    "cursor-api": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/ABS/PATH/TO/cursor-api-mcp",
        "cursor-api-mcp",
        "--read-only"
      ],
      "env": {
        "CURSOR_API_KEY": "crsr_YOUR_KEY_HERE"
      }
    }
  }
}
```

**Full read/write** — omit `--read-only` / `CURSOR_API_READ_ONLY`:

```json
{
  "mcpServers": {
    "cursor-api": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/ABS/PATH/TO/cursor-api-mcp",
        "cursor-api-mcp"
      ],
      "env": {
        "CURSOR_API_KEY": "crsr_YOUR_KEY_HERE"
      }
    }
  }
}
```

Reload MCP in Cursor Settings → MCP after editing.

## Tools

### Always available (read / query)

| Tool | API |
|------|-----|
| `get_api_key_info` | `GET /v1/me` |
| `list_models` | `GET /v1/models` |
| `list_repositories` | `GET /v1/repositories` |
| `list_agents` / `get_agent` | `GET /v1/agents` |
| `list_agent_runs` / `get_agent_run` | `GET /v1/agents/{id}/runs` |
| `get_agent_usage` | `GET /v1/agents/{id}/usage` |
| `list_agent_artifacts` | `GET /v1/agents/{id}/artifacts` |
| `list_team_members` | `GET /teams/members` |
| `get_audit_logs` | `GET /teams/audit-logs` |
| `get_daily_usage_data` | `POST /teams/daily-usage-data` (query) |
| `get_spending_data` | `POST /teams/spend` (query) |
| `get_usage_events` | `POST /teams/filtered-usage-events` (query) |
| `list_team_repo_blocklists` | `GET /settings/repo-blocklists/repos` |
| `list_billing_groups` / `get_billing_group` | `GET /teams/groups` |
| `list_organization_members` | `GET /organizations/members` |

### Write tools (disabled with `--read-only`)

| Tool | API |
|------|-----|
| `create_agent` | `POST /v1/agents` |
| `create_agent_run` | `POST /v1/agents/{id}/runs` |
| `cancel_agent_run` | `POST .../runs/{runId}/cancel` |
| `archive_agent` / `unarchive_agent` | `POST .../archive` / `unarchive` |
| `delete_agent` | `DELETE /v1/agents/{id}` |
| `create_worker_token` | `POST /v1/sub-tokens` |
| `set_user_spend_limit` | `POST /teams/user-spend-limit` |
| `remove_team_member` | `POST /teams/remove-member` |
| `upsert_repo_blocklists` / `delete_repo_blocklist` | blocklist mutate |
| `create_billing_group` / `update_billing_group` / `delete_billing_group` | groups |
| `add_billing_group_members` / `remove_billing_group_members` | group members |
| `sync_organization_team_memberships` | `POST /organizations/team-memberships/sync` |

Cloud Agents tools work with a **user API key** on all plans. Team Admin and
Organization tools need **Enterprise** keys with the right scopes
(e.g. `members:read` for org membership reads).

## Safety

- Prefer `--read-only` unless you need mutations.
- Use the narrowest API key scope that covers your tools.
- Never commit `.env` or paste API keys into chat / git.
- `/v1/repositories` is rate-limited (~1/min); avoid polling loops.

## Development

```bash
uv sync --extra dev
uv run pytest
```

## License

MIT
