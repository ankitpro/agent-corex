"""Tests for agent_core.client — patches httpx directly, no external fixture deps."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from agent_core.client import (
    AgentCoreXClient,
    AgentCoreXError,
    AuthError,
    ConnectionError,
    TimeoutError,
)

BASE = "https://api.v2.agent-corex.com"

QUERY_RESPONSE = {
    "query": "list supabase projects",
    "steps": [
        {
            "intent": "list supabase projects",
            "tool": "list_projects",
            "server": "supabase",
            "inputs": {},
            "missing_inputs": [],
            "ref": "state://abc123",
            "preview": "project-a, project-b",
            "success": True,
            "needs_input": False,
            "skipped": False,
            "skip_reason": None,
            "error": None,
            "latency_ms": 320,
        }
    ],
    "total_latency_ms": 320,
}


def _mock_response(status_code: int, body: dict) -> MagicMock:
    r = MagicMock(spec=httpx.Response)
    r.status_code = status_code
    r.json.return_value = body
    r.text = str(body)
    return r


# ── execute_query ─────────────────────────────────────────────────────────────


def test_execute_query_success():
    with patch("httpx.post", return_value=_mock_response(200, QUERY_RESPONSE)):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
        result = client.execute_query("list supabase projects")
    assert result["query"] == "list supabase projects"
    assert len(result["steps"]) == 1
    assert result["steps"][0]["tool"] == "list_projects"
    assert result["steps"][0]["success"] is True


def test_execute_query_auth_error():
    with patch(
        "httpx.post",
        return_value=_mock_response(401, {"detail": "Invalid API key"}),
    ):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_badkey")
        with pytest.raises(AuthError):
            client.execute_query("test")


def test_execute_query_backend_error():
    with patch(
        "httpx.post",
        return_value=_mock_response(500, {"error": "Internal error"}),
    ):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
        with pytest.raises(AgentCoreXError, match="500"):
            client.execute_query("test")


def test_execute_query_connection_error():
    with patch("httpx.post", side_effect=httpx.ConnectError("Connection refused")):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
        with pytest.raises(ConnectionError):
            client.execute_query("test")


def test_execute_query_timeout():
    with patch("httpx.post", side_effect=httpx.TimeoutException("timed out")):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
        with pytest.raises(TimeoutError):
            client.execute_query("test")


# ── health ────────────────────────────────────────────────────────────────────


def test_health_success():
    with patch(
        "httpx.get",
        return_value=_mock_response(200, {"status": "ok", "version": "2.0"}),
    ):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
        result = client.health()
    assert result["status"] == "ok"
    assert result["version"] == "2.0"


def test_health_no_key():
    """Health check works without an API key."""
    with patch(
        "httpx.get",
        return_value=_mock_response(200, {"status": "ok", "version": "2.0"}),
    ):
        client = AgentCoreXClient(api_url=BASE, api_key=None)
        result = client.health()
    assert result["status"] == "ok"


# ── get_state ─────────────────────────────────────────────────────────────────


def test_get_state_with_prefix():
    with patch(
        "httpx.get",
        return_value=_mock_response(200, {"id": "abc123", "data": {"stdout": "hello"}}),
    ):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
        result = client.get_state("state://abc123")
    assert result["id"] == "abc123"


def test_get_state_without_prefix():
    with patch(
        "httpx.get",
        return_value=_mock_response(200, {"id": "abc123", "data": {}}),
    ):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
        result = client.get_state("abc123")
    assert result["id"] == "abc123"


# ── retrieve ──────────────────────────────────────────────────────────────────


def test_retrieve_passes_params():
    with patch(
        "httpx.get",
        return_value=_mock_response(200, [{"name": "list_projects", "score": 0.9}]),
    ):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
        result = client.retrieve("list supabase projects", top_k=3, debug=True)
    assert len(result) == 1
    assert result[0]["name"] == "list_projects"


# ── auth header ───────────────────────────────────────────────────────────────


def test_auth_header_included():
    """Verify Authorization header is sent when api_key is set."""
    captured = {}

    def fake_get(url, *, params=None, headers=None, timeout=None):
        captured["auth"] = (headers or {}).get("Authorization")
        r = MagicMock(spec=httpx.Response)
        r.status_code = 200
        r.json.return_value = {"status": "ok", "version": "2.0"}
        return r

    with patch("httpx.get", side_effect=fake_get):
        client = AgentCoreXClient(api_url=BASE, api_key="acx_mykey12345")
        client.health()
    assert captured["auth"] == "Bearer acx_mykey12345"


def test_no_auth_header_when_no_key():
    """No Authorization header when api_key is None."""
    captured = {}

    def fake_get(url, *, params=None, headers=None, timeout=None):
        captured["auth"] = (headers or {}).get("Authorization")
        r = MagicMock(spec=httpx.Response)
        r.status_code = 200
        r.json.return_value = {"status": "ok", "version": "2.0"}
        return r

    with patch("httpx.get", side_effect=fake_get):
        client = AgentCoreXClient(api_url=BASE, api_key=None)
        client.health()
    assert captured["auth"] is None
