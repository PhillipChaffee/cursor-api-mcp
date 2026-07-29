# cursor-api-mcp

[MCP](https://modelcontextprotocol.io/) server for the [Cursor HTTP APIs](https://cursor.com/docs/api).

By default the server exposes **read and write** tools (Cloud Agents + Team/Org Admin +
Analytics + Bugbot + AI Code Tracking + Fleet). Pass `--read-only` (or set
`CURSOR_API_READ_ONLY=true`) to register only fetch/query tools.

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

### Cloud Agents (all plans, user API key)

| Tool | API |
|------|-----|
| `get_api_key_info` | `GET /v1/me` |
| `list_models` | `GET /v1/models` |
| `list_repositories` | `GET /v1/repositories` |
| `list_agents` / `get_agent` | `GET /v1/agents` |
| `list_agent_runs` / `get_agent_run` | `GET /v1/agents/{id}/runs` |
| `stream_agent_run` | `GET /v1/agents/{id}/runs/{runId}/stream` |
| `get_agent_usage` | `GET /v1/agents/{id}/usage` |
| `list_agent_artifacts` | `GET /v1/agents/{id}/artifacts` |
| `download_agent_artifact` | `GET /v1/agents/{id}/artifacts/download` |

Write (disabled with `--read-only`):

| Tool | API |
|------|-----|
| `create_agent` | `POST /v1/agents` |
| `create_agent_run` | `POST /v1/agents/{id}/runs` |
| `cancel_agent_run` | `POST .../runs/{runId}/cancel` |
| `archive_agent` / `unarchive_agent` | `POST .../archive` / `unarchive` |
| `delete_agent` | `DELETE /v1/agents/{id}` |
| `create_worker_token` | `POST /v1/sub-tokens` |

### Fleet / private workers (service-account key)

| Tool | API |
|------|-----|
| `list_private_workers` | `GET /v0/private-workers` |
| `get_fleet_summary` | `GET /v0/private-workers/summary` |
| `get_private_worker` | `GET /v0/private-workers/{id}` |
| `list_pending_pool_requests` | `GET /v0/private-workers/pending-requests` |

### Team Admin (Enterprise)

| Tool | API |
|------|-----|
| `list_team_members` | `GET /teams/members` |
| `get_audit_logs` | `GET /teams/audit-logs` |
| `get_daily_usage_data` | `POST /teams/daily-usage-data` |
| `get_spending_data` | `POST /teams/spend` |
| `get_usage_events` | `POST /teams/filtered-usage-events` |
| `list_team_repo_blocklists` | `GET /settings/repo-blocklists/repos` |
| `list_billing_groups` / `get_billing_group` | `GET /teams/groups` |

Write:

| Tool | API |
|------|-----|
| `set_user_spend_limit` | `POST /teams/user-spend-limit` |
| `remove_team_member` | `POST /teams/remove-member` |
| `upsert_repo_blocklists` / `delete_repo_blocklist` | blocklist mutate |
| `create_billing_group` / `update_billing_group` / `delete_billing_group` | groups |
| `add_billing_group_members` / `remove_billing_group_members` | group members |

### Organization Admin (Enterprise org key)

| Tool | API |
|------|-----|
| `list_organization_members` | `GET /organizations/members` |
| `get_organization_pooled_usage` | `POST /organizations/pooled-usage` |
| `get_organization_usage_events` | `POST /organizations/filtered-usage-events` |
| `get_organization_daily_usage_data` | `POST /organizations/daily-usage-data` |
| `get_organization_spending_data` | `POST /organizations/spend` |
| `list_organization_groups` / `get_organization_group` | `GET /organizations/groups` |
| `list_organization_group_members` | `GET .../groups/{id}/members` |

Write:

| Tool | API |
|------|-----|
| `sync_organization_team_memberships` | `POST /organizations/team-memberships/sync` |
| `add_organization_group_members` | `POST .../members/bulk-add` |
| `remove_organization_group_members` | `POST .../members/bulk-remove` |

### Analytics (Enterprise)

| Tool | API |
|------|-----|
| `get_team_analytics` | `GET /analytics/team/{metric}` |
| `get_analytics_by_user` | `GET /analytics/by-user/{metric}` |

`metric` is allowlisted (e.g. `agent-edits`, `tabs`, `dau`, `models`, `bugbot`,
`bugbot-reviews`, `conversation-insights`, …). See tool docstrings for the full lists.

### AI Code Tracking (Enterprise, alpha)

| Tool | API |
|------|-----|
| `list_ai_code_commits` | `GET /analytics/ai-code/commits` |
| `download_ai_code_commits_csv` | `GET /analytics/ai-code/commits.csv` |
| `list_ai_code_changes` | `GET /analytics/ai-code/changes` |
| `download_ai_code_changes_csv` | `GET /analytics/ai-code/changes.csv` |
| `get_ai_code_commit_details` | `GET /analytics/ai-code/commits/{hash}` |

### Bugbot (Enterprise)

| Tool | API |
|------|-----|
| `list_bugbot_repos` | `GET /bugbot/repos` |

Write:

| Tool | API |
|------|-----|
| `trigger_bugbot_review` | `POST /bugbot/review` |
| `update_bugbot_repo` | `POST /bugbot/repo/update` |
| `update_bugbot_user_access` | `POST /bugbot/user/update` |

## Safety

- Prefer `--read-only` unless you need mutations.
- Use the narrowest API key scope that covers your tools.
- Never commit `.env` or paste API keys into chat / git.
- `/v1/repositories` is rate-limited (~1/min); avoid polling loops.
- `create_worker_token` redacts `accessToken` in tool results (mint raw JWTs outside MCP).
- `stream_agent_run` buffers SSE until close/timeout — prefer `get_agent_run` for watches.
- CSV download tools return the body as `csv_text` (can be large).

## Development

```bash
uv sync --extra dev
uv run pytest
```

## License

MIT
