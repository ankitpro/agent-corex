"""
Registry — persistent store for installed packs and MCP servers.

File: ~/.agent-corex/registry.json

Schema:
{
  "packs": {
    "youtube-productivity": {
      "name": "youtube-productivity",
      "mcp_servers": ["filesystem", "youtube"],
      "tools": ["summarize_video", "download_transcript"],
      "installed_at": "2024-01-01T00:00:00Z"
    }
  },
  "mcp_servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {},
      "installed_at": "2024-01-01T00:00:00Z",
      "source": "pack:youtube-productivity"
    }
  }
}
"""

from __future__ import annotations

import json
import os
import pathlib
import stat
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# Mirror the existing config directory so all state lives in one place
REGISTRY_DIR: pathlib.Path = pathlib.Path.home() / ".agent-corex"
REGISTRY_FILE: pathlib.Path = REGISTRY_DIR / "registry.json"

_EMPTY: Dict[str, Any] = {"packs": {}, "mcp_servers": {}}


# ── I/O helpers ───────────────────────────────────────────────────────────────


def _ensure_dir() -> None:
    """Create ~/.agent-corex/ with restricted permissions if it doesn't exist."""
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        REGISTRY_DIR.chmod(stat.S_IRWXU)


def _load() -> Dict[str, Any]:
    """Return parsed registry; returns a clean empty registry on any error."""
    if not REGISTRY_FILE.exists():
        return {"packs": {}, "mcp_servers": {}}
    try:
        data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
        data.setdefault("packs", {})
        data.setdefault("mcp_servers", {})
        return data
    except (json.JSONDecodeError, OSError):
        return {"packs": {}, "mcp_servers": {}}


def _save(data: Dict[str, Any]) -> None:
    """Atomically write registry to disk."""
    _ensure_dir()
    tmp = REGISTRY_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    if os.name != "nt":
        tmp.chmod(stat.S_IRUSR | stat.S_IWUSR)
    tmp.replace(REGISTRY_FILE)


def _now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Pack operations ───────────────────────────────────────────────────────────


def get_packs() -> Dict[str, Any]:
    """Return all installed packs as ``{name: metadata}``."""
    return _load()["packs"]


def get_pack(name: str) -> Optional[Dict[str, Any]]:
    """Return a single installed pack's metadata, or ``None`` if not installed."""
    return _load()["packs"].get(name)


def add_pack(
    name: str,
    mcp_servers: List[str],
    tools: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Register a pack in the registry.

    Args:
        name:        Pack slug (e.g. ``"youtube-productivity"``).
        mcp_servers: List of MCP server slugs the pack requires.
        tools:       Optional list of tool names the pack exposes.
        extra:       Any additional metadata from the API response to persist.
    """
    data = _load()
    entry: Dict[str, Any] = {
        "name": name,
        "mcp_servers": mcp_servers,
        "tools": tools or [],
        "installed_at": _now_iso(),
    }
    if extra:
        entry.update({k: v for k, v in extra.items() if k not in entry})
    data["packs"][name] = entry
    _save(data)


def remove_pack(name: str) -> bool:
    """
    Remove a pack from the registry.

    Returns:
        ``True`` if the pack was present and removed, ``False`` if it wasn't installed.
    """
    data = _load()
    if name not in data["packs"]:
        return False
    del data["packs"][name]
    _save(data)
    return True


# ── MCP server operations ─────────────────────────────────────────────────────


def get_servers() -> Dict[str, Any]:
    """Return all installed MCP servers as ``{name: config}``."""
    return _load()["mcp_servers"]


def get_server(name: str) -> Optional[Dict[str, Any]]:
    """Return a single MCP server's config, or ``None`` if not installed."""
    return _load()["mcp_servers"].get(name)


def add_server(
    name: str,
    command: str,
    args: List[str],
    env: Optional[Dict[str, str]] = None,
    source: str = "manual",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Register an MCP server in the registry.

    Args:
        name:    Server slug (e.g. ``"filesystem"``).
        command: Executable to launch the server (e.g. ``"npx"``).
        args:    Arguments list (e.g. ``["-y", "@modelcontextprotocol/server-filesystem"]``).
        env:     Optional environment variables to inject into the server process.
        source:  Where this server was installed from — ``"manual"`` or ``"pack:<name>"``.
        extra:   Any extra metadata from the API to persist alongside.
    """
    data = _load()
    entry: Dict[str, Any] = {
        "command": command,
        "args": args,
        "env": env or {},
        "installed_at": _now_iso(),
        "source": source,
    }
    if extra:
        entry.update({k: v for k, v in extra.items() if k not in entry})
    data["mcp_servers"][name] = entry
    _save(data)


def remove_server(name: str) -> bool:
    """
    Remove an MCP server from the registry.

    Returns:
        ``True`` if the server was present and removed, ``False`` otherwise.
    """
    data = _load()
    if name not in data["mcp_servers"]:
        return False
    del data["mcp_servers"][name]
    _save(data)
    return True


def server_is_installed(name: str) -> bool:
    """Return ``True`` if the named MCP server is in the registry."""
    return name in _load()["mcp_servers"]


# ── Bulk helpers used by the gateway ─────────────────────────────────────────


def get_all_server_configs() -> List[Dict[str, Any]]:
    """
    Return registry MCP server configs in the format expected by MCPLoader.

    Each entry looks like::

        {
          "name": "filesystem",
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-filesystem"],
          "env": {}
        }
    """
    servers = get_servers()
    result: List[Dict[str, Any]] = []
    for name, cfg in servers.items():
        result.append(
            {
                "name": name,
                "command": cfg["command"],
                "args": cfg.get("args", []),
                "env": cfg.get("env", {}),
            }
        )
    return result
