"""Tests for agent_core.cli.main — uses Typer's CliRunner."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agent_core.cli.main import app
from agent_core.client import AgentCoreXError, AuthError, ConnectionError
from agent_core.mcp.manager import MCPManager
from agent_core.mcp.registry import MCPRegistry
from agent_core.mcp.local_store import LocalStore

runner = CliRunner()

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


# ── version ───────────────────────────────────────────────────────────────────


def test_version():
    from agent_core import __version__

    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "agent-corex" in result.output
    assert __version__ in result.output


# ── run ───────────────────────────────────────────────────────────────────────


def test_run_success():
    """Test remote/premium execution path (--remote flag)."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = QUERY_RESPONSE

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.local_config.is_premium", return_value=False),
    ):
        result = runner.invoke(app, ["run", "list supabase projects", "--remote"])

    assert result.exit_code == 0
    assert "list_projects" in result.output
    assert "project-a" in result.output


def test_run_debug_shows_details():
    """Test debug output on remote path."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = QUERY_RESPONSE

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.local_config.is_premium", return_value=False),
    ):
        result = runner.invoke(app, ["run", "list supabase projects", "--debug", "--remote"])

    assert result.exit_code == 0
    assert "Intent" in result.output or "intent" in result.output.lower()
    assert "list_projects" in result.output
    assert "320" in result.output  # latency


def test_run_auth_error():
    """Auth error on remote path."""
    mock_client = MagicMock()
    mock_client.execute_query.side_effect = AuthError("Invalid API key")

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.local_config.is_premium", return_value=False),
    ):
        result = runner.invoke(app, ["run", "test query", "--remote"])

    assert result.exit_code == 1
    assert "agent-corex login" in result.output


def test_run_connection_error():
    """Connection error on remote path."""
    mock_client = MagicMock()
    mock_client.execute_query.side_effect = ConnectionError("refused")

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.local_config.is_premium", return_value=False),
    ):
        result = runner.invoke(app, ["run", "test query", "--remote"])

    assert result.exit_code == 1


def test_run_needs_input_step():
    """Needs-input step on remote path."""
    response = {
        "query": "deploy service",
        "steps": [
            {
                "intent": "deploy service",
                "tool": "deploy_service",
                "server": "railway",
                "inputs": {},
                "missing_inputs": ["service_name", "region"],
                "ref": None,
                "preview": None,
                "success": False,
                "needs_input": True,
                "skipped": False,
                "skip_reason": None,
                "error": None,
                "latency_ms": 50,
            }
        ],
        "total_latency_ms": 50,
    }
    mock_client = MagicMock()
    mock_client.execute_query.return_value = response

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.local_config.is_premium", return_value=False),
    ):
        result = runner.invoke(app, ["run", "deploy service", "--remote"])

    assert result.exit_code == 0
    assert "needs input" in result.output.lower() or "service_name" in result.output


# ── config ────────────────────────────────────────────────────────────────────


def test_config_set_api_url(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_core.local_config.CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr("agent_core.local_config.CONFIG_DIR", tmp_path)

    result = runner.invoke(app, ["config", "set", "api_url=http://localhost:8000"])
    assert result.exit_code == 0
    assert "api_url" in result.output


def test_config_set_invalid_key(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_core.local_config.CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr("agent_core.local_config.CONFIG_DIR", tmp_path)

    result = runner.invoke(app, ["config", "set", "unknown_key=value"])
    assert result.exit_code == 1


def test_config_set_missing_equals():
    result = runner.invoke(app, ["config", "set", "noequals"])
    assert result.exit_code == 1


def test_config_show(tmp_path, monkeypatch):
    import json

    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"api_url": "https://api.example.com", "api_key": "acx_abcdefghij"}))
    monkeypatch.setattr("agent_core.local_config.CONFIG_FILE", cfg)
    monkeypatch.setattr("agent_core.local_config.CONFIG_DIR", tmp_path)

    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "https://api.example.com" in result.output
    assert "acx_abcd" in result.output  # masked — first 8 chars visible
    assert "abcdefghij" not in result.output  # full key must not appear


# ── login ─────────────────────────────────────────────────────────────────────


def test_login_valid_key(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_core.local_config.CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr("agent_core.local_config.CONFIG_DIR", tmp_path)

    mock_client = MagicMock()
    mock_client.health.return_value = {"status": "ok", "version": "2.0"}

    with patch("agent_core.cli.main.AgentCoreXClient", return_value=mock_client):
        result = runner.invoke(app, ["login", "--key", "acx_validkey12345"])

    assert result.exit_code == 0
    assert "Logged in" in result.output


def test_login_invalid_format():
    result = runner.invoke(app, ["login", "--key", "badkey"])
    assert result.exit_code == 1
    assert "Invalid key format" in result.output


def test_login_key_rejected_by_backend(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_core.local_config.CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr("agent_core.local_config.CONFIG_DIR", tmp_path)

    mock_client = MagicMock()
    mock_client.health.side_effect = AuthError("rejected")

    with patch("agent_core.cli.main.AgentCoreXClient", return_value=mock_client):
        result = runner.invoke(app, ["login", "--key", "acx_rejectedkey123"])

    assert result.exit_code == 1
    assert "rejected" in result.output.lower()


# ── logout ────────────────────────────────────────────────────────────────────


def test_logout(tmp_path, monkeypatch):
    import json

    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({"api_key": "acx_somekey12345"}))
    monkeypatch.setattr("agent_core.local_config.CONFIG_FILE", cfg)
    monkeypatch.setattr("agent_core.local_config.CONFIG_DIR", tmp_path)

    result = runner.invoke(app, ["logout"])
    assert result.exit_code == 0
    assert "Logged out" in result.output
    remaining = json.loads(cfg.read_text())
    assert "api_key" not in remaining


# ── health ────────────────────────────────────────────────────────────────────


def test_health_ok():
    mock_client = MagicMock()
    mock_client.health.return_value = {"status": "ok", "version": "2.0"}

    with patch("agent_core.cli.main._make_client", return_value=mock_client):
        result = runner.invoke(app, ["health"])

    assert result.exit_code == 0
    assert "ok" in result.output


# ── run (hybrid / free tier) ──────────────────────────────────────────────────


PLAN_RESPONSE = {
    "query": "list railway projects",
    "steps": [
        {
            "intent": "list railway projects",
            "tool": "list_projects",
            "server": "railway",
            "inputs": {},
            "missing_inputs": [],
            "ref": None,
            "preview": None,
            "success": False,
            "needs_input": False,
            "skipped": False,
            "skip_reason": None,
            "error": None,
            "latency_ms": 10,
        }
    ],
    "total_latency_ms": 10,
}


def test_run_free_tier_success():
    """Free tier: plan_query + local execution + submit_result."""
    mock_client = MagicMock()
    mock_client.plan_query.return_value = PLAN_RESPONSE
    mock_client.submit_result.return_value = {"ref": "state://abc", "preview": "project-a"}

    mock_mgr = MagicMock()
    mock_mgr.servers = {"railway": MagicMock()}
    mock_mgr.call_tool.return_value = {"content": "project-a"}

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.local_config.is_premium", return_value=False),
        patch("agent_core.mcp.manager.MCPManager.from_local_store", return_value=mock_mgr),
    ):
        result = runner.invoke(app, ["run", "list railway projects"])

    assert result.exit_code == 0
    mock_client.plan_query.assert_called_once_with("list railway projects")
    mock_mgr.call_tool.assert_called_once_with("railway", "list_projects", {})
    mock_mgr.shutdown_all.assert_called_once()


def test_run_forced_remote():
    """--remote flag forces backend execution regardless of is_premium."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = QUERY_RESPONSE

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.local_config.is_premium", return_value=False),
    ):
        result = runner.invoke(app, ["run", "list supabase projects", "--remote"])

    assert result.exit_code == 0
    mock_client.execute_query.assert_called_once()
    mock_client.plan_query.assert_not_called()


def test_run_premium_uses_remote():
    """Premium users use execute_query (backend execution) by default."""
    mock_client = MagicMock()
    mock_client.execute_query.return_value = QUERY_RESPONSE

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.local_config.is_premium", return_value=True),
    ):
        result = runner.invoke(app, ["run", "list supabase projects"])

    assert result.exit_code == 0
    mock_client.execute_query.assert_called_once()


def test_run_free_missing_server():
    """Free tier: error when planned server is not installed locally."""
    mock_client = MagicMock()
    mock_client.plan_query.return_value = PLAN_RESPONSE

    mock_mgr = MagicMock()
    mock_mgr.servers = {}  # railway not installed

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.local_config.is_premium", return_value=False),
        patch("agent_core.mcp.manager.MCPManager.from_local_store", return_value=mock_mgr),
    ):
        result = runner.invoke(app, ["run", "list railway projects"])

    assert result.exit_code == 1


# ── mcp subcommands ───────────────────────────────────────────────────────────


def test_mcp_list():
    mock_client = MagicMock()
    mock_client.list_available_servers.return_value = [
        {"name": "railway", "description": "Deploy", "status": "verified"},
        {"name": "github", "description": "GitHub", "status": "verified"},
    ]

    with patch("agent_core.cli.main._make_client", return_value=mock_client):
        result = runner.invoke(app, ["mcp", "list"])

    assert result.exit_code == 0
    assert "railway" in result.output
    assert "github" in result.output


def test_mcp_add_known_server(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_core.local_config.get_api_key", lambda: "acx_testkey12345")
    monkeypatch.setattr("agent_core.local_config.is_logged_in", lambda: True)

    mock_client = MagicMock()
    mock_client.add_server.return_value = {"server_name": "railway"}

    mock_store = MagicMock()
    mock_registry = MagicMock()
    mock_registry.get.return_value = {
        "name": "railway",
        "command": "npx",
        "args": ["-y", "@railway/mcp-server"],
        "env_required": [],
    }

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.mcp.registry.MCPRegistry.get", mock_registry.get),
        patch("agent_core.mcp.local_store.LocalStore.add_server", mock_store.add_server),
        patch("agent_core.mcp.local_store.LocalStore.mark_installed", mock_store.mark_installed),
    ):
        result = runner.invoke(app, ["mcp", "add", "railway"])

    assert result.exit_code == 0
    assert "railway" in result.output


def test_mcp_add_unknown_server(tmp_path, monkeypatch):
    monkeypatch.setattr("agent_core.local_config.get_api_key", lambda: "acx_testkey12345")
    monkeypatch.setattr("agent_core.local_config.is_logged_in", lambda: True)

    with patch("agent_core.mcp.registry.MCPRegistry.get", return_value=None):
        result = runner.invoke(app, ["mcp", "add", "nonexistent"])

    assert result.exit_code == 1


def test_mcp_add_requires_login(monkeypatch):
    monkeypatch.setattr("agent_core.local_config.get_api_key", lambda: None)
    monkeypatch.setattr("agent_core.local_config.is_logged_in", lambda: False)
    result = runner.invoke(app, ["mcp", "add", "railway"])
    assert result.exit_code == 1
    assert "login" in result.output.lower()


def test_mcp_remove(monkeypatch):
    monkeypatch.setattr("agent_core.local_config.get_api_key", lambda: "acx_testkey12345")
    monkeypatch.setattr("agent_core.local_config.is_logged_in", lambda: True)

    mock_client = MagicMock()
    mock_client.remove_server.return_value = {"removed": "railway"}

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch("agent_core.mcp.local_store.LocalStore.remove_server", return_value=True),
        patch("agent_core.mcp.local_store.LocalStore.mark_removed"),
    ):
        result = runner.invoke(app, ["mcp", "remove", "railway"])

    assert result.exit_code == 0
    assert "railway" in result.output


def test_mcp_show(monkeypatch):
    monkeypatch.setattr("agent_core.local_config.get_api_key", lambda: "acx_testkey12345")
    monkeypatch.setattr("agent_core.local_config.is_logged_in", lambda: True)

    mock_client = MagicMock()
    mock_client.list_user_servers.return_value = [{"server_name": "railway"}]

    with (
        patch("agent_core.cli.main._make_client", return_value=mock_client),
        patch(
            "agent_core.mcp.local_store.LocalStore.list_servers", return_value=["railway", "github"]
        ),
    ):
        result = runner.invoke(app, ["mcp", "show"])

    assert result.exit_code == 0
    assert "railway" in result.output
