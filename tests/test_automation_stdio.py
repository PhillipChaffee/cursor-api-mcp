from __future__ import annotations

import asyncio
import json
import sys
from copy import deepcopy
from textwrap import dedent

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def test_automation_stdio_catalog_and_calls(tmp_path) -> None:
    automation_id = "ed868f34-6b32-4431-8874-38bf6d781d85"
    snapshot = {
        "workflow": {
            "workflow": {
                "automationId": automation_id,
                "name": "Original",
                "enabled": True,
                "workflow": {
                    "triggers": [{"futureTrigger": {"enabled": True}}],
                    "actions": [{"mcp": {"server": {"name": "tools", "id": "123"}}}],
                    "prompts": [{"prompt": "First"}, {"prompt": "Second", "model": "model-a"}],
                    "future": [False, None, ""],
                },
            },
            "ownerName": "Example owner",
            "mcpAuthStates": [{"serverName": "tools", "state": "authenticated"}],
        },
    }
    expected = deepcopy(snapshot)
    expected["workflow"]["workflow"]["workflow"]["prompts"][1]["prompt"] = "Changed"
    expected["workflow"]["workflow"]["name"] = ""
    expected["workflow"]["workflow"]["enabled"] = False
    bootstrap = dedent(f"""
        import json
        from functools import partial
        import httpx
        from cursor_api_mcp.server import main

        snapshot = json.loads({json.dumps(snapshot)!r})
        expected = json.loads({json.dumps(expected)!r})

        def handle(request):
            assert request.url.host == "api2.cursor.sh"
            assert request.method == "POST"
            body = json.loads(request.content)
            if request.url.path == "/auth/exchange_user_api_key":
                assert request.headers["authorization"] == "Bearer key_stdio-secret"
                assert body == {{}}
                return httpx.Response(200, json={{
                    "accessToken": "access-secret", "refreshToken": "refresh-secret",
                }})
            assert request.headers["authorization"] == "Bearer access-secret"
            assert request.headers["connect-protocol-version"] == "1"
            if request.url.path == "/aiserver.v1.AutomationsService/GetAutomation":
                assert body == {{"automationId": {automation_id!r}, "teamId": 42}}
                return httpx.Response(200, json=snapshot)
            assert request.url.path == "/aiserver.v1.AutomationsService/UpdateAutomation"
            assert body == {{
                "automationId": {automation_id!r}, "name": "", "enabled": False,
                "workflow": expected["workflow"]["workflow"]["workflow"],
            }}
            snapshot.update(expected)
            return httpx.Response(200, json=snapshot)

        httpx.Client = partial(httpx.Client, transport=httpx.MockTransport(handle))
        main()
    """)
    params = StdioServerParameters(
        command=sys.executable,
        args=["-c", bootstrap, "--read-only", "--allow-automation-writes"],
        env={
            "CURSOR_API_KEY": "key_stdio-secret",
            "CURSOR_API_BASE_URL": "https://untrusted.invalid",
            "CURSOR_API_READ_ONLY": "false",
            "CURSOR_API_ALLOW_AUTOMATION_WRITES": "false",
        },
    )

    async def exercise(errlog) -> None:
        async with stdio_client(params, errlog=errlog) as (reader, writer):
            async with ClientSession(reader, writer, read_timeout_seconds=10) as session:
                initialized = await session.initialize()
                assert "Only update_automation" in initialized.instructions
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                assert {"get_automation", "update_automation", "list_agents"} <= tools.keys()
                assert (
                    not {"create_agent", "set_user_spend_limit", "trigger_bugbot_review"}
                    & tools.keys()
                )
                assert set(tools["update_automation"].input_schema["properties"]) == {
                    "automation_id",
                    "name",
                    "description",
                    "enabled",
                    "prompt",
                    "prompt_index",
                    "team_id",
                }
                assert (
                    "Concurrent edits can be overwritten" in tools["update_automation"].description
                )
                read = await session.call_tool(
                    "get_automation", {"automation_id": automation_id, "team_id": 42}
                )
                assert read.structured_content == snapshot
                update = await session.call_tool(
                    "update_automation",
                    {
                        "automation_id": automation_id,
                        "team_id": 42,
                        "prompt_index": 1,
                        "prompt": "Changed",
                        "name": "",
                        "enabled": False,
                    },
                )
                assert update.structured_content == expected
                reread = await session.call_tool(
                    "get_automation", {"automation_id": automation_id, "team_id": 42}
                )
                assert reread.structured_content == expected
                assert all(
                    secret not in str(update)
                    for secret in ["key_stdio-secret", "access-secret", "refresh-secret"]
                )

    with (tmp_path / "stderr.txt").open("w+") as errlog:
        asyncio.run(asyncio.wait_for(exercise(errlog), timeout=20))
        errlog.seek(0)
        logs = errlog.read()
        assert all(
            secret not in logs for secret in ["key_stdio-secret", "access-secret", "refresh-secret"]
        )
