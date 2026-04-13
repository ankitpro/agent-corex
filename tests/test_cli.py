"""Tests for agent_core.cli.main — uses Typer's CliRunner."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from agent_core.cli.main import app
from agent_core.client import AgentCoreXError, AuthError, ConnectionError

runner = CliRunner(mix_stderr=False)

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
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "agent-corex" in result.output
    assert "4.0.0" in result.output


# ── run ───────────────────────────────────────────────────────────────────────


def test_run_success():
    mock_client = MagicMock()
    mock_client.execute_query.return_value = QUERY_RESPONSE

    with patch("agent_core.cli.main._make_client", return_value=mock_client):
        result = runner.invoke(app, ["run", "list supabase projects"])

    assert result.exit_code == 0
    assert "list_projects" in result.output
    assert "project-a" in result.output


def test_run_debug_shows_details():
    mock_client = MagicMock()
    mock_client.execute_query.return_value = QUERY_RESPONSE

    with patch("agent_core.cli.main._make_client", return_value=mock_client):
        result = runner.invoke(app, ["run", "list supabase projects", "--debug"])

    assert result.exit_code == 0
    assert "Intent" in result.output or "intent" in result.output.lower()
    assert "list_projects" in result.output
    assert "320" in result.output  # latency


def test_run_auth_error():
    mock_client = MagicMock()
    mock_client.execute_query.side_effect = AuthError("Invalid API key")

    with patch("agent_core.cli.main._make_client", return_value=mock_client):
        result = runner.invoke(app, ["run", "test query"])

    assert result.exit_code == 1
    assert "agent-corex login" in result.stderr or "agent-corex login" in result.output


def test_run_connection_error():
    mock_client = MagicMock()
    mock_client.execute_query.side_effect = ConnectionError("refused")

    with patch("agent_core.cli.main._make_client", return_value=mock_client):
        result = runner.invoke(app, ["run", "test query"])

    assert result.exit_code == 1


def test_run_needs_input_step():
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

    with patch("agent_core.cli.main._make_client", return_value=mock_client):
        result = runner.invoke(app, ["run", "deploy service"])

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
