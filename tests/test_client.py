"""Tests for agent_core.client — mocks httpx responses."""

import pytest
import httpx

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


def _make_transport(responses: list[httpx.Response]) -> httpx.MockTransport:
    """Build a mock transport that returns responses in order."""
    responses_iter = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        return next(responses_iter)

    return httpx.MockTransport(handler)


def _client(responses: list[httpx.Response], api_key: str = "acx_testkey12345") -> AgentCoreXClient:
    """Return a client that uses a mock transport."""
    c = AgentCoreXClient(api_url=BASE, api_key=api_key)
    # Patch _post and _get to use mock transport via httpx.Client
    c._mock_responses = responses  # type: ignore[attr-defined]
    return c


# ── execute_query ─────────────────────────────────────────────────────────────


def test_execute_query_success(respx_mock):
    respx_mock.post(f"{BASE}/execute/query").mock(
        return_value=httpx.Response(200, json=QUERY_RESPONSE)
    )
    client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
    result = client.execute_query("list supabase projects")
    assert result["query"] == "list supabase projects"
    assert len(result["steps"]) == 1
    assert result["steps"][0]["tool"] == "list_projects"
    assert result["steps"][0]["success"] is True


def test_execute_query_auth_error(respx_mock):
    respx_mock.post(f"{BASE}/execute/query").mock(
        return_value=httpx.Response(401, json={"detail": "Invalid API key"})
    )
    client = AgentCoreXClient(api_url=BASE, api_key="acx_badkey")
    with pytest.raises(AuthError):
        client.execute_query("test")


def test_execute_query_backend_error(respx_mock):
    respx_mock.post(f"{BASE}/execute/query").mock(
        return_value=httpx.Response(500, json={"error": "Internal error"})
    )
    client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
    with pytest.raises(AgentCoreXError, match="500"):
        client.execute_query("test")


def test_execute_query_connection_error(respx_mock):
    respx_mock.post(f"{BASE}/execute/query").mock(side_effect=httpx.ConnectError("refused"))
    client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
    with pytest.raises(ConnectionError):
        client.execute_query("test")


def test_execute_query_timeout(respx_mock):
    respx_mock.post(f"{BASE}/execute/query").mock(
        side_effect=httpx.ReadTimeout("timed out", request=None)
    )
    client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
    with pytest.raises(TimeoutError):
        client.execute_query("test")


# ── health ────────────────────────────────────────────────────────────────────


def test_health_success(respx_mock):
    respx_mock.get(f"{BASE}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok", "version": "2.0"})
    )
    client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
    result = client.health()
    assert result["status"] == "ok"
    assert result["version"] == "2.0"


def test_health_no_key(respx_mock):
    """Health check should work without an API key (no auth header)."""
    respx_mock.get(f"{BASE}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok", "version": "2.0"})
    )
    client = AgentCoreXClient(api_url=BASE, api_key=None)
    result = client.health()
    assert result["status"] == "ok"


# ── get_state ─────────────────────────────────────────────────────────────────


def test_get_state_with_prefix(respx_mock):
    respx_mock.get(f"{BASE}/state/abc123").mock(
        return_value=httpx.Response(200, json={"id": "abc123", "data": {"stdout": "hello"}})
    )
    client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
    result = client.get_state("state://abc123")
    assert result["id"] == "abc123"


def test_get_state_without_prefix(respx_mock):
    respx_mock.get(f"{BASE}/state/abc123").mock(
        return_value=httpx.Response(200, json={"id": "abc123", "data": {}})
    )
    client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
    result = client.get_state("abc123")
    assert result["id"] == "abc123"


# ── retrieve ──────────────────────────────────────────────────────────────────


def test_retrieve_passes_params(respx_mock):
    respx_mock.get(f"{BASE}/retrieve/").mock(
        return_value=httpx.Response(200, json=[{"name": "list_projects", "score": 0.9}])
    )
    client = AgentCoreXClient(api_url=BASE, api_key="acx_testkey12345")
    result = client.retrieve("list supabase projects", top_k=3, debug=True)
    assert len(result) == 1
    assert result[0]["name"] == "list_projects"


# ── auth header ───────────────────────────────────────────────────────────────


def test_auth_header_included(respx_mock):
    """Verify Authorization header is sent when api_key is set."""
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("authorization")
        return httpx.Response(200, json={"status": "ok", "version": "2.0"})

    respx_mock.get(f"{BASE}/health").mock(side_effect=handler)
    client = AgentCoreXClient(api_url=BASE, api_key="acx_mykey12345")
    client.health()
    assert captured["auth"] == "Bearer acx_mykey12345"
