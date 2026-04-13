"""Tests for agent_core.mcp.manager."""

import pytest
from unittest.mock import MagicMock, patch

from agent_core.mcp.manager import MCPManager
from agent_core.mcp.client import MCPClient


def _make_started_client(name="railway", tools=None):
    """Return a pre-initialized MCPClient mock."""
    client = MagicMock(spec=MCPClient)
    client.name = name
    client._initialized = True
    client.list_tools.return_value = tools or [
        {"name": "list_projects", "description": "List projects"},
    ]
    client.call_tool.return_value = {"content": "project-a"}
    return client


# ── from_local_store ──────────────────────────────────────────────────────────


def test_from_local_store_creates_clients(tmp_path):
    import json
    mcp_json = tmp_path / "mcp.json"
    mcp_json.write_text(json.dumps({
        "mcpServers": {
            "railway": {"command": "npx", "args": ["-y", "@railway/mcp-server"]},
            "github": {"command": "npx", "args": ["-y", "@github/mcp"]},
        }
    }))

    from agent_core.mcp.local_store import LocalStore
    with patch("agent_core.mcp.manager.LocalStore") as MockStore:
        mock_store = MagicMock()
        mock_store.load_mcp_config.return_value = {
            "railway": {"command": "npx", "args": ["-y", "@railway/mcp-server"]},
            "github": {"command": "npx", "args": ["-y", "@github/mcp"]},
        }
        MockStore.return_value = mock_store
        mgr = MCPManager.from_local_store()

    assert "railway" in mgr.servers
    assert "github" in mgr.servers


# ── call_tool ─────────────────────────────────────────────────────────────────


def test_call_tool_success():
    mgr = MCPManager()
    client = _make_started_client("railway")
    mgr.register("railway", client)

    result = mgr.call_tool("railway", "list_projects", {})
    assert result == {"content": "project-a"}
    client.call_tool.assert_called_once_with("list_projects", {})


def test_call_tool_unknown_server():
    mgr = MCPManager()
    with pytest.raises(ValueError, match="not in MCPManager"):
        mgr.call_tool("vercel", "list_projects", {})


def test_call_tool_starts_uninitialized_client():
    mgr = MCPManager()
    client = MagicMock(spec=MCPClient)
    client.name = "railway"
    client._initialized = False
    client.call_tool.return_value = {"content": "ok"}
    mgr.register("railway", client)

    result = mgr.call_tool("railway", "list_projects", {})
    client.start.assert_called_once()
    assert result == {"content": "ok"}


def test_call_tool_propagates_exception():
    mgr = MCPManager()
    client = _make_started_client("railway")
    client.call_tool.side_effect = RuntimeError("tool failed")
    mgr.register("railway", client)

    with pytest.raises(RuntimeError, match="tool failed"):
        mgr.call_tool("railway", "list_projects", {})


# ── shutdown_all ──────────────────────────────────────────────────────────────


def test_shutdown_all():
    mgr = MCPManager()
    c1 = _make_started_client("railway")
    c2 = _make_started_client("github")
    mgr.register("railway", c1)
    mgr.register("github", c2)
    mgr.shutdown_all()
    c1.stop.assert_called_once()
    c2.stop.assert_called_once()


def test_shutdown_all_tolerates_errors():
    mgr = MCPManager()
    c1 = _make_started_client("railway")
    c1.stop.side_effect = Exception("stop failed")
    mgr.register("railway", c1)
    mgr.shutdown_all()  # should not raise
