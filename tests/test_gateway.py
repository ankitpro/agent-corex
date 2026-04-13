"""Tests for agent_core.gateway.gateway_server — JSON-RPC handler unit tests."""

import json
from unittest.mock import MagicMock, patch

import pytest

from agent_core.gateway.gateway_server import (
    _dispatch,
    _format_response,
    _handle_initialize,
    _handle_tools_call,
    _handle_tools_list,
    SERVER_NAME,
    SERVER_VERSION,
    TOOLS,
)
from agent_core.client import AuthError, ConnectionError

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
    assert "tools" in r["capabilities"]
    # Must NOT expose resources or prompts
    assert "resources" not in r["capabilities"]
    assert "prompts" not in r["capabilities"]


# ── tools/call ────────────────────────────────────────────────────────────────


def test_handle_tools_call_execute_query_success():
    mock_client = MagicMock()
    mock_client.execute_query.return_value = {
        "query": "list projects",
        "steps": [
            {
                "tool": "list_projects",
                "server": "supabase",
                "intent": "list supabase projects",
                "inputs": {},
                "missing_inputs": [],
                "ref": "state://abc",
                "preview": "proj-a, proj-b",
                "success": True,
                "needs_input": False,
                "skipped": False,
                "skip_reason": None,
                "error": None,
                "latency_ms": 200,
            }
        ],
        "total_latency_ms": 200,
    }

    with patch("agent_core.gateway.gateway_server.AgentCoreXClient", return_value=mock_client):
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
    mock_client.execute_query.side_effect = AuthError("invalid key")

    with patch("agent_core.gateway.gateway_server.AgentCoreXClient", return_value=mock_client):
        result = _handle_tools_call(1, {"name": "execute_query", "arguments": {"query": "test"}})

    assert result["result"]["isError"] is True
    assert "Authentication" in result["result"]["content"][0]["text"]


def test_handle_tools_call_connection_error():
    mock_client = MagicMock()
    mock_client.execute_query.side_effect = ConnectionError("refused")

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
