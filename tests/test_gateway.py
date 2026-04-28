"""Tests for agent_core.gateway.gateway_server — JSON-RPC handler unit tests."""

import json
from unittest.mock import MagicMock, patch

import pytest

from agent_core.gateway import gateway_server as _gw
from agent_core.gateway.gateway_server import (
    _build_dynamic_tools,
    _dispatch,
    _format_response,
    _handle_initialize,
    _handle_prompts_get,
    _handle_prompts_list,
    _handle_resources_list,
    _handle_resources_read,
    _handle_tools_call,
    _handle_tools_list,
    SERVER_NAME,
    SERVER_VERSION,
    TOOLS,
)
from agent_core.client import AuthError, ConnectionError


@pytest.fixture
def _stub_payload(monkeypatch):
    """Stub _get_capability_payload so tests don't hit the real backend."""
    payload = {
        "servers": {
            "railway": {
                "capabilities": [
                    {
                        "name": "list_projects",
                        "description": "List Railway projects.",
                        "examples": ["list railway projects"],
                        "tool_ref": "railway.list_projects",
                    }
                ]
            }
        },
        "skills": [],
        "templates": [
            {
                "pattern": "list railway projects",
                "server": "railway",
                "tool": "list_projects",
            }
        ],
        "installed_servers": ["railway"],
    }
    monkeypatch.setattr(_gw, "_get_capability_payload", lambda: payload)
    return payload


# ── Tool list ─────────────────────────────────────────────────────────────────


def test_tools_list_returns_three_tools():
    tool_names = [t["name"] for t in TOOLS]
    assert len(TOOLS) == 3
    assert "execute_query" in tool_names
    assert "discover_capabilities" in tool_names
    assert "search_tools" in tool_names


def test_tools_list_has_query_input():
    execute_tool = next(t for t in TOOLS if t["name"] == "execute_query")
    schema = execute_tool["inputSchema"]
    assert "query" in schema["properties"]
    assert schema["required"] == ["query"]


def test_handle_tools_list():
    result = _handle_tools_list(1, {})
    assert result["id"] == 1
    tools = result["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert len(tools) == 3
    assert "execute_query" in tool_names
    assert "discover_capabilities" in tool_names
    assert "search_tools" in tool_names


# ── Initialize ────────────────────────────────────────────────────────────────


def test_handle_initialize():
    result = _handle_initialize(1, {})
    assert result["id"] == 1
    r = result["result"]
    assert r["serverInfo"]["name"] == SERVER_NAME
    assert r["serverInfo"]["version"] == SERVER_VERSION
    # v4.1.0: advertise tools + prompts + resources so hosts query all three.
    # prompts exposes the capability context; resources exposes the raw JSON.
    assert "tools" in r["capabilities"]
    assert "prompts" in r["capabilities"]
    assert "resources" in r["capabilities"]


# ── tools/call ────────────────────────────────────────────────────────────────


def test_handle_tools_call_execute_query_success():
    mock_client = MagicMock()
    mock_client.plan_query.return_value = {
        "query": "list projects",
        "steps": [
            {
                "tool": "list_projects",
                "server": "supabase",
                "intent": "list supabase projects",
                "inputs": {},
                "missing_inputs": [],
                "success": False,
                "needs_input": False,
                "skipped": False,
                "skip_reason": None,
                "error": None,
                "latency_ms": 0,
            }
        ],
        "total_latency_ms": 0,
    }
    mock_client.submit_result.return_value = {"ref": "state://abc", "preview": "proj-a, proj-b"}

    mock_mgr = MagicMock()
    mock_mgr.call_tool.return_value = [{"type": "text", "text": "proj-a, proj-b"}]

    with patch("agent_core.gateway.gateway_server.AgentCoreXClient", return_value=mock_client):
        with patch("agent_core.mcp.manager.MCPManager") as mock_mcp_manager:
            mock_mcp_manager.from_local_store.return_value = mock_mgr
            result = _handle_tools_call(
                1, {"name": "execute_query", "arguments": {"query": "list projects"}}
            )

    assert result["id"] == 1
    content = result["result"]["content"]
    assert len(content) == 1
    assert content[0]["type"] == "text"
    assert "list_projects" in content[0]["text"]
    assert result["result"]["isError"] is False


def test_handle_tools_call_unknown_tool():
    result = _handle_tools_call(1, {"name": "unknown_tool", "arguments": {}})
    assert result["error"]["code"] == -32601


def test_handle_tools_call_empty_query():
    result = _handle_tools_call(1, {"name": "execute_query", "arguments": {"query": ""}})
    assert result["result"]["isError"] is True
    assert "required" in result["result"]["content"][0]["text"].lower()


def test_handle_tools_call_auth_error():
    mock_client = MagicMock()
    mock_client.plan_query.side_effect = AuthError("invalid key")

    with patch("agent_core.gateway.gateway_server.AgentCoreXClient", return_value=mock_client):
        result = _handle_tools_call(1, {"name": "execute_query", "arguments": {"query": "test"}})

    assert result["result"]["isError"] is True
    assert "Authentication" in result["result"]["content"][0]["text"]


def test_handle_tools_call_connection_error():
    mock_client = MagicMock()
    mock_client.plan_query.side_effect = ConnectionError("refused")

    with patch("agent_core.gateway.gateway_server.AgentCoreXClient", return_value=mock_client):
        result = _handle_tools_call(1, {"name": "execute_query", "arguments": {"query": "test"}})

    assert result["result"]["isError"] is True
    assert "backend" in result["result"]["content"][0]["text"].lower()


# ── dispatch ──────────────────────────────────────────────────────────────────


def test_dispatch_ping():
    result = _dispatch({"jsonrpc": "2.0", "id": 1, "method": "ping"})
    assert result is not None
    assert result["result"] == {}


def test_dispatch_notification_returns_none():
    # Notifications have no "id" field
    result = _dispatch({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
    assert result is None


def test_dispatch_unknown_method():
    result = _dispatch({"jsonrpc": "2.0", "id": 5, "method": "unknown/method"})
    assert result["error"]["code"] == -32601


# ── _format_response ──────────────────────────────────────────────────────────


def test_format_response_success():
    response = {
        "query": "list projects",
        "steps": [
            {
                "tool": "list_projects",
                "success": True,
                "needs_input": False,
                "skipped": False,
                "preview": "proj-a, proj-b",
                "ref": "state://abc",
                "error": None,
                "skip_reason": None,
            }
        ],
        "total_latency_ms": 200,
    }
    text = _format_response(response)
    assert "list_projects" in text
    assert "OK" in text
    assert "proj-a" in text
    assert "200ms" in text


def test_format_response_needs_input():
    response = {
        "query": "deploy",
        "steps": [
            {
                "tool": "deploy_service",
                "success": False,
                "needs_input": True,
                "skipped": False,
                "missing_inputs": ["service_name"],
                "preview": None,
                "ref": None,
                "error": None,
                "skip_reason": None,
            }
        ],
        "total_latency_ms": 30,
    }
    text = _format_response(response)
    assert "needs input" in text
    assert "service_name" in text


def test_format_response_skipped():
    response = {
        "query": "do something",
        "steps": [
            {
                "tool": "some_tool",
                "success": False,
                "needs_input": False,
                "skipped": True,
                "skip_reason": "low_selection_confidence",
                "preview": None,
                "ref": None,
                "error": None,
                "missing_inputs": [],
            }
        ],
        "total_latency_ms": 10,
    }
    text = _format_response(response)
    assert "skipped" in text
    assert "low_selection_confidence" in text


def test_format_response_failed():
    response = {
        "query": "bad query",
        "steps": [
            {
                "tool": "some_tool",
                "success": False,
                "needs_input": False,
                "skipped": False,
                "error": "execution_failed",
                "preview": None,
                "ref": None,
                "skip_reason": None,
                "missing_inputs": [],
            }
        ],
        "total_latency_ms": 50,
    }
    text = _format_response(response)
    assert "FAILED" in text
    assert "execution_failed" in text


# ── Dynamic tool descriptions (v4.1.0+) ──────────────────────────────────────


def test_build_dynamic_tools_injects_installed_servers(_stub_payload):
    tools = _build_dynamic_tools(_stub_payload)
    assert len(tools) == 3
    execute = next(t for t in tools if t["name"] == "execute_query")
    desc = execute["description"]
    # Must enumerate installed server
    assert "railway" in desc
    # Must steer away from shell
    assert "shell" in desc.lower() or "bash" in desc.lower()
    # Must include an example phrasing
    assert "list railway projects" in desc


def test_build_dynamic_tools_no_servers_leaves_base_description():
    empty = {"servers": {}, "installed_servers": [], "templates": []}
    tools = _build_dynamic_tools(empty)
    execute = next(t for t in tools if t["name"] == "execute_query")
    # Base description doesn't mention specific servers
    assert "railway" not in execute["description"]


def test_handle_tools_list_returns_dynamic(_stub_payload):
    result = _handle_tools_list(1, {})
    tools = result["result"]["tools"]
    execute = next(t for t in tools if t["name"] == "execute_query")
    assert "railway" in execute["description"]


# ── prompts/* ────────────────────────────────────────────────────────────────


def test_handle_prompts_list_has_capabilities_prompt(_stub_payload):
    result = _handle_prompts_list(1, {})
    prompts = result["result"]["prompts"]
    assert len(prompts) == 1
    assert prompts[0]["name"] == "agent_corex_capabilities"


def test_handle_prompts_get_returns_system_block(_stub_payload):
    result = _handle_prompts_get(1, {"name": "agent_corex_capabilities"})
    messages = result["result"]["messages"]
    assert len(messages) == 1
    text = messages[0]["content"]["text"]
    assert "railway" in text
    assert "list_projects" in text


def test_handle_prompts_get_unknown_name_errors(_stub_payload):
    result = _handle_prompts_get(1, {"name": "nope"})
    assert "error" in result


# ── resources/* ──────────────────────────────────────────────────────────────


def test_handle_resources_list_has_capabilities_resource(_stub_payload):
    result = _handle_resources_list(1, {})
    resources = result["result"]["resources"]
    assert len(resources) == 1
    assert resources[0]["uri"] == "agent-corex://capabilities"
    assert resources[0]["mimeType"] == "application/json"


def test_handle_resources_read_returns_json_payload(_stub_payload):
    result = _handle_resources_read(1, {"uri": "agent-corex://capabilities"})
    contents = result["result"]["contents"]
    text = contents[0]["text"]
    parsed = json.loads(text)
    assert "railway" in parsed["servers"]


def test_handle_resources_read_unknown_uri_errors(_stub_payload):
    result = _handle_resources_read(1, {"uri": "agent-corex://nope"})
    assert "error" in result
