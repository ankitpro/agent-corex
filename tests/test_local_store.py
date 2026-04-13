"""Tests for agent_core.mcp.local_store."""

import json
import pytest

from agent_core.mcp.local_store import LocalStore


def _store(tmp_path):
    return LocalStore(base_dir=tmp_path)


# ── add / remove / list ───────────────────────────────────────────────────────


def test_add_server_creates_mcp_json(tmp_path):
    store = _store(tmp_path)
    store.add_server("railway", "npx", ["-y", "@railway/mcp-server"])
    data = json.loads((tmp_path / "mcp.json").read_text())
    assert "railway" in data["mcpServers"]
    assert data["mcpServers"]["railway"]["command"] == "npx"


def test_add_server_with_env(tmp_path):
    store = _store(tmp_path)
    store.add_server("railway", "npx", ["-y", "@railway/mcp-server"], env={"RAILWAY_TOKEN": "tok"})
    data = json.loads((tmp_path / "mcp.json").read_text())
    assert data["mcpServers"]["railway"]["env"]["RAILWAY_TOKEN"] == "tok"


def test_remove_server_returns_true(tmp_path):
    store = _store(tmp_path)
    store.add_server("railway", "npx", [])
    result = store.remove_server("railway")
    assert result is True
    data = json.loads((tmp_path / "mcp.json").read_text())
    assert "railway" not in data["mcpServers"]


def test_remove_server_returns_false_when_not_present(tmp_path):
    store = _store(tmp_path)
    assert store.remove_server("nonexistent") is False


def test_list_servers_empty(tmp_path):
    store = _store(tmp_path)
    assert store.list_servers() == []


def test_list_servers_after_add(tmp_path):
    store = _store(tmp_path)
    store.add_server("railway", "npx", [])
    store.add_server("github", "npx", [])
    names = store.list_servers()
    assert set(names) == {"railway", "github"}


# ── load_raw / save_raw round-trip ────────────────────────────────────────────


def test_load_raw_missing_returns_default(tmp_path):
    store = _store(tmp_path)
    data = store.load_raw()
    assert data == {"mcpServers": {}}


def test_round_trip(tmp_path):
    store = _store(tmp_path)
    store.add_server("railway", "npx", ["-y", "@railway/mcp-server"])
    data = store.load_mcp_config()
    assert data["railway"]["args"] == ["-y", "@railway/mcp-server"]


# ── installed_servers.json ────────────────────────────────────────────────────


def test_mark_installed(tmp_path):
    store = _store(tmp_path)
    store.mark_installed("railway")
    assert store.is_installed("railway")


def test_mark_removed(tmp_path):
    store = _store(tmp_path)
    store.mark_installed("railway")
    store.mark_removed("railway")
    assert not store.is_installed("railway")


def test_is_installed_false_when_no_file(tmp_path):
    store = _store(tmp_path)
    assert not store.is_installed("railway")
