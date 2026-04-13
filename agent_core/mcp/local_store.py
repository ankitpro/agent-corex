"""
LocalStore — reads and writes ~/.agent-corex/mcp.json and installed_servers.json.

mcp.json schema:
    {
      "mcpServers": {
        "railway": {
          "command": "npx",
          "args": ["-y", "@railway/mcp-server"],
          "env": {"RAILWAY_TOKEN": "..."}  # optional
        }
      }
    }

installed_servers.json schema:
    {"railway": {"installed_at": "2026-04-13T..."}, ...}
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _config_dir() -> Path:
    return Path.home() / ".agent-corex"


class LocalStore:
    """Manages the user's local MCP server configuration."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._dir = base_dir or _config_dir()
        self._mcp_file = self._dir / "mcp.json"
        self._installed_file = self._dir / "installed_servers.json"

    # ---- mcp.json ----

    def load_raw(self) -> Dict[str, Any]:
        """Return the full mcp.json contents (creates empty file if missing)."""
        if not self._mcp_file.exists():
            return {"mcpServers": {}}
        with open(self._mcp_file, encoding="utf-8") as f:
            return json.load(f)

    def load_mcp_config(self) -> Dict[str, Dict]:
        """Return just the mcpServers dict: {server_name: {command, args, env?}}."""
        data = self.load_raw()
        return data.get("mcpServers", {})

    def save_raw(self, data: Dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._mcp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def add_server(
        self, name: str, command: str, args: List[str], env: Dict[str, str] | None = None
    ) -> None:
        """Add or update a server in mcp.json."""
        data = self.load_raw()
        entry: Dict[str, Any] = {"command": command, "args": args}
        if env:
            entry["env"] = env
        data.setdefault("mcpServers", {})[name] = entry
        self.save_raw(data)

    def remove_server(self, name: str) -> bool:
        """Remove a server from mcp.json. Returns True if it existed."""
        data = self.load_raw()
        servers = data.get("mcpServers", {})
        if name not in servers:
            return False
        del servers[name]
        data["mcpServers"] = servers
        self.save_raw(data)
        return True

    def list_servers(self) -> List[str]:
        """Return names of all locally configured servers."""
        return list(self.load_mcp_config().keys())

    # ---- installed_servers.json ----

    def load_installed(self) -> Dict[str, Any]:
        if not self._installed_file.exists():
            return {}
        with open(self._installed_file, encoding="utf-8") as f:
            return json.load(f)

    def mark_installed(self, name: str) -> None:
        installed = self.load_installed()
        installed[name] = {"installed_at": datetime.now(timezone.utc).isoformat()}
        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._installed_file, "w", encoding="utf-8") as f:
            json.dump(installed, f, indent=2)

    def mark_removed(self, name: str) -> None:
        installed = self.load_installed()
        installed.pop(name, None)
        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._installed_file, "w", encoding="utf-8") as f:
            json.dump(installed, f, indent=2)

    def is_installed(self, name: str) -> bool:
        return name in self.load_installed()
