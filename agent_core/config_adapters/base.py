"""
Abstract base class for MCP config adapters.

An adapter can:
  - read the current mcpServers config from a tool's config file
  - inject a new MCP server entry (merging, never overwriting the full file)
  - remove an MCP server entry
  - backup before mutating

Config files always contain a top-level "mcpServers" object:
  {
    "mcpServers": {
      "agent-corex": {
        "command": "agent-corex",
        "args": ["serve"]
      }
    }
  }
"""

import json
import pathlib
import shutil
from abc import ABC, abstractmethod
from datetime import datetime


class BaseAdapter(ABC):
    """Read / write the mcpServers block in a tool's config file."""

    tool_name: str = ""

    @abstractmethod
    def config_path(self) -> pathlib.Path | None:
        """Return the config file path, or None if not determinable."""

    # ── Internal helpers ───────────────────────────────────────────────────────

    def _read(self) -> dict:
        p = self.config_path()
        if p is None or not p.exists():
            return {}
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def _write(self, data: dict) -> None:
        p = self.config_path()
        if p is None:
            raise RuntimeError(f"Cannot determine config path for {self.tool_name}")
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(p)

    def _backup(self) -> pathlib.Path | None:
        p = self.config_path()
        if p is None or not p.exists():
            return None
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = p.with_name(f"{p.stem}.{stamp}.bak")
        shutil.copy2(p, backup)
        return backup

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_servers(self) -> dict:
        """Return the current mcpServers dict (may be empty)."""
        return self._read().get("mcpServers", {})

    def has_server(self, server_name: str) -> bool:
        return server_name in self.get_servers()

    def inject_server(
        self, server_name: str, server_def: dict, backup: bool = True
    ) -> pathlib.Path | None:
        """
        Add or overwrite *server_name* in mcpServers.
        Merges with existing config — never overwrites the full file.
        Returns the backup path if a backup was created.
        """
        bak = self._backup() if backup else None
        data = self._read()
        data.setdefault("mcpServers", {})[server_name] = server_def
        self._write(data)
        return bak

    def remove_server(self, server_name: str, backup: bool = True) -> pathlib.Path | None:
        """Remove *server_name* from mcpServers. No-op if absent."""
        if not self.has_server(server_name):
            return None
        bak = self._backup() if backup else None
        data = self._read()
        data.get("mcpServers", {}).pop(server_name, None)
        self._write(data)
        return bak
