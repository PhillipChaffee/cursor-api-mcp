from __future__ import annotations

import asyncio
import json
from collections import deque
from copy import deepcopy
from functools import partial
from typing import Any

import httpx
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from cursor_api_mcp.automations import AutomationsClient
from cursor_api_mcp.config import ServerConfig
from cursor_api_mcp.server import build_server

AUTOMATION_ID = "ed868f34-6b32-4431-8874-38bf6d781d85"
RPC = "https://api2.cursor.sh/aiserver.v1.AutomationsService/"
EXCHANGE = "https://api2.cursor.sh/auth/exchange_user_api_key"
SNAPSHOT = {
    "workflow": {
        "workflow": {
            "automationId": AUTOMATION_ID,
            "name": "Review",
            "enabled": True,
            "updatedAt": "1793059200000",
            "workflow": {
                "triggers": [{"cron": {"expression": "0 9 * * *", "future": True}}],
                "actions": [{"mcp": {"server": {"name": "tools", "id": "9007199254740993"}}}],
                "prompts": [
                    {
                        "prompt": "Review the changes",
                        "effortLevel": "PROMPT_EFFORT_LEVEL_HIGH",
                        "model": "example-model",
                        "isFilter": False,
                        "runMode": "PROMPT_RUN_MODE_CONTINUE",
                        "suppressSlackReaction": True,
                        "modelSelection": {"model": "example-model", "future": [1, 2]},
                    },
                    {"prompt": "Report the result", "future": {"preserve": None}},
                ],
                "gitConfig": {"branch": "main", "repoUrl": "https://github.com/example/repo"},
                "agentOptions": {"skipInstall": True},
                "memoryEnabled": False,
                "slackNotifiedChannels": ["C123"],
                "managedConfig": {"unknown": {"items": [False, "", None]}},
                "disabledDefaultTools": ["FUTURE_TOOL"],
                "grokSessionId": "server-owned",
                "futureWorkflowField": {"keep": True},
            },
        },
        "userId": 17,
        "ownerName": "Example owner",
        "teamId": 42,
        "mcpAuthStates": [{"serverName": "tools", "state": "MCP_AUTH_STATE_AUTHENTICATED"}],
        "futureOwnerField": "kept",
    },
    "futureResponseField": ["kept"],
}


@pytest.fixture
def http(monkeypatch: pytest.MonkeyPatch):
    responses: deque[httpx.Response | Exception] = deque()
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        response = responses.popleft()
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(
        httpx, "Client", partial(httpx.Client, transport=httpx.MockTransport(handle))
    )
    monkeypatch.setenv("CURSOR_API_KEY", "session-test-token")
    monkeypatch.setenv("CURSOR_API_BASE_URL", "https://untrusted.invalid")
    return responses, requests


def call_tool(tool_name: str = "update_automation", **arguments: Any) -> dict[str, Any]:
    server = build_server(ServerConfig(read_only=True, allow_automation_writes=True))
    result = asyncio.run(server.call_tool(tool_name, {"automation_id": AUTOMATION_ID, **arguments}))
    assert isinstance(result.structured_content, dict)
    return result.structured_content


@pytest.mark.parametrize(
    "key", ["key_test-secret", "crsr_test-secret", "  Bearer crsr_test-secret  "]
)
def test_key_exchange_and_token_reuse(http, key: str) -> None:
    responses, requests = http
    responses.extend(
        [
            httpx.Response(
                200, json={"accessToken": "  access-secret  ", "refreshToken": "refresh-secret"}
            ),
            httpx.Response(200, json=SNAPSHOT),
            httpx.Response(200, json=SNAPSHOT),
        ]
    )
    client = AutomationsClient(api_key=key)
    assert client.call("GetAutomation", {"automationId": AUTOMATION_ID}) == SNAPSHOT
    assert (
        client.call("UpdateAutomation", {"automationId": AUTOMATION_ID, "enabled": False})
        == SNAPSHOT
    )
    assert [str(request.url) for request in requests] == [
        EXCHANGE,
        RPC + "GetAutomation",
        RPC + "UpdateAutomation",
    ]
    assert requests[0].headers["authorization"] == "Bearer " + key.strip().removeprefix("Bearer ")
    assert json.loads(requests[0].content) == {}
    for request in requests:
        assert request.method == "POST"
        assert request.headers["content-type"] == "application/json"
        assert request.headers["connect-protocol-version"] == "1"
        assert request.extensions["timeout"]["read"] == 60.0
    assert all(
        request.headers["authorization"] == "Bearer access-secret" for request in requests[1:]
    )


@pytest.mark.parametrize(
    "token", ["session-secret", "  session-secret  ", "  bEaReR session-secret  "]
)
def test_session_token_is_used_directly(http, token: str) -> None:
    responses, requests = http
    responses.append(httpx.Response(200, json=SNAPSHOT))
    assert AutomationsClient(api_key=token).call("GetAutomation", {}) == SNAPSHOT
    assert len(requests) == 1
    assert str(requests[0].url) == RPC + "GetAutomation"
    assert requests[0].headers["authorization"] == "Bearer session-secret"


@pytest.mark.parametrize(
    "token", [None, "", "  ", "Bearer ", "bad\nsecret", "bad\x00secret", "badésecret"]
)
def test_invalid_credentials_never_make_requests(http, monkeypatch, token) -> None:
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)
    with pytest.raises(ValueError):
        AutomationsClient(api_key=token)
    assert not http[1]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"accessToken": None},
        {"accessToken": 7},
        {"accessToken": ""},
        {"accessToken": "bad\nsecret", "refreshToken": "refresh-secret"},
    ],
)
def test_malformed_exchange_prevents_rpc(http, monkeypatch, payload) -> None:
    responses, requests = http
    monkeypatch.setenv("CURSOR_API_KEY", "key_secret")
    responses.append(httpx.Response(200, json=payload))
    result = call_tool(enabled=False)
    assert result["error"] is True
    assert "secret" not in json.dumps(result)
    assert [str(request.url) for request in requests] == [EXCHANGE]


@pytest.mark.parametrize("stage", ["exchange", "get", "update"])
@pytest.mark.parametrize(
    "failure",
    ["redirect", "unauthorized", "forbidden", "throttle", "server", "html", "list", "timeout"],
)
def test_failures_are_bounded_private_and_not_retried(
    http, monkeypatch, caplog, stage, failure
) -> None:
    responses, requests = http
    monkeypatch.setenv("CURSOR_API_KEY", "key_secret")
    secret = "key_secret access-secret refresh-secret"
    if stage != "exchange":
        responses.append(
            httpx.Response(
                200, json={"accessToken": "access-secret", "refreshToken": "refresh-secret"}
            )
        )
    failures = {
        "redirect": httpx.Response(
            307, headers={"Location": "https://untrusted.invalid/" + secret}
        ),
        "forbidden": httpx.Response(403, json={"message": secret * 1000}),
        "unauthorized": httpx.Response(401, json={"message": secret}),
        "throttle": httpx.Response(429, json={"message": secret}),
        "server": httpx.Response(503, json={"error": secret}),
        "html": httpx.Response(200, text="<html>" + secret),
        "list": httpx.Response(200, json=[secret]),
        "timeout": httpx.ReadTimeout(secret),
    }
    responses.append(failures[failure])
    result = call_tool("get_automation") if stage == "get" else call_tool(enabled=False)
    assert result["error"] is True
    assert len(result["message"]) < 250
    output = json.dumps(result) + caplog.text
    assert all(value not in output for value in secret.split())
    assert len(requests) == (1 if stage == "exchange" else 2)
    if failure in {"redirect", "unauthorized", "forbidden", "throttle", "server"}:
        assert result["status_code"] == failures[failure].status_code
    if stage == "update":
        assert "inspect it before retrying" in result["message"]


@pytest.mark.parametrize("team_id", [None, 42, 2**31 - 1])
def test_get_preserves_authorized_response(http, team_id) -> None:
    responses, requests = http
    responses.append(httpx.Response(200, json=SNAPSHOT))
    assert call_tool("get_automation", team_id=team_id) == SNAPSHOT
    expected = {"automationId": AUTOMATION_ID}
    if team_id is not None:
        expected["teamId"] = team_id
    assert json.loads(requests[0].content) == expected


@pytest.mark.parametrize(
    "edits",
    [
        {"enabled": False},
        {"name": ""},
        {"description": ""},
        {"name": "Changed", "enabled": True, "description": "Details"},
    ],
)
def test_metadata_update_sends_only_selected_fields_without_read(http, edits) -> None:
    responses, requests = http
    responses.append(httpx.Response(200, json=SNAPSHOT))
    assert call_tool(team_id=42, **edits) == SNAPSHOT
    assert len(requests) == 1
    assert str(requests[0].url) == RPC + "UpdateAutomation"
    assert json.loads(requests[0].content) == {"automationId": AUTOMATION_ID, **edits}


@pytest.mark.parametrize("index", [0, 1, None])
def test_prompt_edit_preserves_complete_fresh_workflow(http, monkeypatch, index) -> None:
    responses, requests = http
    monkeypatch.setenv("CURSOR_API_KEY", "crsr_secret")
    snapshot = deepcopy(SNAPSHOT)
    workflow = snapshot["workflow"]["workflow"]["workflow"]
    if index is None:
        workflow["prompts"].pop()
    expected = deepcopy(workflow)
    expected["prompts"][index or 0]["prompt"] = ""
    updated = deepcopy(snapshot)
    updated["workflow"]["workflow"]["workflow"] = expected
    responses.extend(
        [
            httpx.Response(200, json={"accessToken": "access-secret"}),
            httpx.Response(200, json=snapshot),
            httpx.Response(200, json=updated),
        ]
    )
    assert call_tool(prompt="", prompt_index=index, enabled=False, team_id=42) == updated
    assert [str(request.url) for request in requests] == [
        EXCHANGE,
        RPC + "GetAutomation",
        RPC + "UpdateAutomation",
    ]
    assert json.loads(requests[1].content) == {"automationId": AUTOMATION_ID, "teamId": 42}
    assert json.loads(requests[2].content) == {
        "automationId": AUTOMATION_ID,
        "enabled": False,
        "workflow": expected,
    }
    assert workflow["prompts"][index or 0]["prompt"] != ""


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"prompt_index": 0},
        {"prompt": "new", "prompt_index": -1},
        {"enabled": False, "automation_id": "../../bad"},
        {"name": "x", "team_id": 0},
        {"prompt": "new", "team_id": -1},
        {"prompt": "new", "team_id": 2**31},
    ],
)
def test_invalid_edit_arguments_do_not_send_http(http, arguments) -> None:
    assert call_tool(**arguments)["error"] is True
    assert not http[1]


@pytest.mark.parametrize("field", ["team_id", "prompt_index"])
@pytest.mark.parametrize("value", [True, "1", 1.5])
def test_indices_reject_coercion(http, field, value) -> None:
    with pytest.raises(ToolError):
        call_tool(prompt="new", **{field: value})
    assert not http[1]


@pytest.mark.parametrize(
    "arguments", [{"automation_id": "bad"}, {"team_id": 0}, {"team_id": 2**31}]
)
def test_invalid_get_arguments_do_not_send_http(http, arguments) -> None:
    assert call_tool("get_automation", **arguments)["error"] is True
    assert not http[1]


@pytest.mark.parametrize("index", [None, 2, 1000000])
def test_ambiguous_or_out_of_bounds_prompt_index_prevents_write(http, index) -> None:
    responses, requests = http
    responses.append(httpx.Response(200, json=SNAPSHOT))
    assert call_tool(prompt="new", prompt_index=index)["error"] is True
    assert [str(request.url) for request in requests] == [RPC + "GetAutomation"]


def test_restricted_response_is_preserved_but_cannot_supply_an_edit(http) -> None:
    responses, requests = http
    restricted = {"restrictedSummary": {"automationId": AUTOMATION_ID, "name": "Limited"}}
    responses.extend([httpx.Response(200, json=restricted), httpx.Response(200, json=restricted)])
    assert call_tool("get_automation") == restricted
    assert call_tool(prompt="new", prompt_index=0, enabled=False)["error"] is True
    assert all(str(request.url) == RPC + "GetAutomation" for request in requests)


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(403, json={"message": "Forbidden"}),
        httpx.Response(200, text="Not JSON"),
        httpx.Response(200, json=["Not an object"]),
    ],
)
def test_failed_prompt_read_prevents_write(http, response) -> None:
    responses, requests = http
    responses.append(response)
    assert call_tool(prompt="new", prompt_index=0, name="Changed")["error"] is True
    assert [str(request.url) for request in requests] == [RPC + "GetAutomation"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"workflow": []},
        {"workflow": {"workflow": {"automationId": "wrong"}}},
        {"workflow": {"workflow": {"automationId": AUTOMATION_ID}}},
        {**SNAPSHOT, "restrictedSummary": {}},
        {"workflow": SNAPSHOT["workflow"]["workflow"]},
    ],
)
def test_incomplete_or_mismatched_response_prevents_write(http, payload) -> None:
    responses, requests = http
    responses.append(httpx.Response(200, json=payload))
    assert call_tool(prompt="new", prompt_index=0)["error"] is True
    assert [str(request.url) for request in requests] == [RPC + "GetAutomation"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("triggers", {}),
        ("actions", None),
        ("actions", [None]),
        ("prompts", {}),
        ("prompts", []),
        ("prompts", ["old"]),
        ("prompts", [{"prompt": 42}]),
    ],
)
def test_malformed_workflow_prevents_write(http, field, value) -> None:
    responses, requests = http
    snapshot = deepcopy(SNAPSHOT)
    snapshot["workflow"]["workflow"]["workflow"][field] = value
    responses.append(httpx.Response(200, json=snapshot))
    assert call_tool(prompt="new", prompt_index=0)["error"] is True
    assert [str(request.url) for request in requests] == [RPC + "GetAutomation"]


def test_protobuf_omitted_empty_fields_are_preserved(http) -> None:
    responses, requests = http
    snapshot = {
        "workflow": {"workflow": {"automationId": AUTOMATION_ID, "workflow": {"prompts": [{}]}}}
    }
    responses.extend([httpx.Response(200, json=snapshot), httpx.Response(200, json=SNAPSHOT)])
    assert call_tool(prompt="new") == SNAPSHOT
    assert json.loads(requests[-1].content) == {
        "automationId": AUTOMATION_ID,
        "workflow": {"prompts": [{"prompt": "new"}]},
    }
