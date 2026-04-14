"""
Unit tests for the thin agent_core.capabilities client module.

Covers:
    - fetch() caches the backend payload on disk
    - fetch() degrades gracefully when the backend raises
    - build_system_block() renders a compact markdown block
    - invalidate() drops the cache file
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_core import capabilities


# ---- Fixtures ----

@pytest.fixture
def tmp_home(tmp_path, monkeypatch):
    """Point Path.home() at a temp dir so cache writes are isolated."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path


class _FakeClient:
    def __init__(self, payload=None, raise_exc=None):
        self._payload = payload or {
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
                    "execution": "railway projects",
                    "args": {},
                }
            ],
            "installed_servers": ["railway"],
        }
        self._raise = raise_exc
        self.calls = 0

    def get_capabilities(self, servers=None):
        self.calls += 1
        if self._raise:
            raise self._raise
        return self._payload


def _seed_installed(tmp_home, name="railway"):
    cfg_dir = tmp_home / ".agent-corex"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "installed_servers.json").write_text(
        f'{{"{name}": {{"installed_at": "2026-01-01T00:00:00Z"}}}}'
    )


# ---- fetch ----

def test_fetch_caches_payload(tmp_home):
    _seed_installed(tmp_home)
    client = _FakeClient()

    payload = capabilities.fetch(client, use_cache=False)
    assert "servers" in payload and "railway" in payload["servers"]

    # Second call hits the on-disk cache — no new backend call
    payload2 = capabilities.fetch(client, use_cache=True)
    assert client.calls == 1
    assert payload2["servers"] == payload["servers"]


def test_fetch_no_installed_servers_returns_empty(tmp_home):
    client = _FakeClient()
    payload = capabilities.fetch(client, use_cache=False)
    assert payload["servers"] == {}
    assert payload["installed_servers"] == []
    assert client.calls == 0  # did not call backend


def test_fetch_backend_failure_falls_back(tmp_home):
    _seed_installed(tmp_home)
    client = _FakeClient(raise_exc=RuntimeError("boom"))
    payload = capabilities.fetch(client, use_cache=False)
    # Graceful degradation: empty servers but installed list preserved
    assert payload["servers"] == {}
    assert payload["installed_servers"] == ["railway"]


# ---- build_system_block ----

def test_build_system_block_renders_capabilities_and_templates():
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
        "templates": [
            {"pattern": "list railway projects", "server": "railway", "tool": "list_projects"}
        ],
    }
    block = capabilities.build_system_block(payload)
    assert "## Available MCP capabilities" in block
    assert "### railway" in block
    assert "list_projects — List Railway projects" in block
    assert 'e.g. "list railway projects"' in block
    assert "Templates (instant execution)" in block
    assert '"list railway projects" → railway.list_projects' in block


def test_build_system_block_empty_payload_returns_empty_string():
    assert capabilities.build_system_block({"servers": {}, "templates": []}) == ""


# ---- invalidate ----

def test_invalidate_removes_cache_file(tmp_home):
    _seed_installed(tmp_home)
    capabilities.fetch(_FakeClient(), use_cache=False)
    cache_file = tmp_home / ".agent-corex" / ".cache" / "capabilities.json"
    assert cache_file.exists()

    capabilities.invalidate()
    assert not cache_file.exists()
