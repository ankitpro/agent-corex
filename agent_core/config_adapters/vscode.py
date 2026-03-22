"""
Adapter for VS Code's user-level settings.json.

VS Code (1.99+) stores MCP servers at:

    settings.json → mcp → servers → { "server-name": { ... } }

This is structurally different from Claude/Cursor which use a top-level
"mcpServers" key. This adapter overrides get_servers / inject_server /
remove_server to navigate the nested path correctly, while leaving every
other key in settings.json completely untouched.

Server definition shape expected by VS Code:

    {
      "type": "stdio",
      "command": "agent-corex",
      "args": ["serve"]
    }
"""

import json
import pathlib
import shutil
from datetime import datetime

from agent_core.config_adapters.base import BaseAdapter


class VSCodeAdapter(BaseAdapter):
    """
    Read / write the mcp.servers block in VS Code's settings.json.

    Inherits _read / _write / _backup from BaseAdapter.
    Overrides the public API to use the VS Code-specific key path.
    """

    tool_name: str = "VS Code"
    _detector_class: type | None = None  # set by subclasses

    def config_path(self) -> pathlib.Path | None:
        if self._detector_class is None:
            raise NotImplementedError("Subclasses must set _detector_class")
        return self._detector_class().config_path()

    # ── Helpers for the nested mcp.servers path ────────────────────────────

    def _get_mcp_servers(self, data: dict) -> dict:
        """Return the mcp.servers dict from a parsed settings.json."""
        return data.get("mcp", {}).get("servers", {})

    def _set_mcp_server(self, data: dict, server_name: str, server_def: dict) -> dict:
        """Merge one server entry into data['mcp']['servers'], return modified data."""
        mcp_block = data.setdefault("mcp", {})
        servers = mcp_block.setdefault("servers", {})
        servers[server_name] = server_def
        return data

    def _del_mcp_server(self, data: dict, server_name: str) -> dict:
        """Remove one server entry from data['mcp']['servers'], return modified data."""
        data.get("mcp", {}).get("servers", {}).pop(server_name, None)
        return data

    # ── Public API (overrides BaseAdapter) ────────────────────────────────

    def get_servers(self) -> dict:
        """Return the current mcp.servers dict (may be empty)."""
        return self._get_mcp_servers(self._read())

    def has_server(self, server_name: str) -> bool:
        return server_name in self.get_servers()

    def inject_server(
        self, server_name: str, server_def: dict, backup: bool = True
    ) -> pathlib.Path | None:
        """
        Add or update *server_name* inside settings.json → mcp → servers.

        All other settings.json keys (themes, keybindings, extensions, …)
        are preserved verbatim. A backup is created before any write.
        """
        bak = self._backup() if backup else None
        data = self._read()
        data = self._set_mcp_server(data, server_name, server_def)
        self._write(data)
        return bak

    def remove_server(
        self, server_name: str, backup: bool = True
    ) -> pathlib.Path | None:
        """Remove *server_name* from mcp.servers. No-op if absent."""
        if not self.has_server(server_name):
            return None
        bak = self._backup() if backup else None
        data = self._read()
        data = self._del_mcp_server(data, server_name)
        self._write(data)
        return bak


# ── Concrete adapters for each VS Code variant ─────────────────────────────

class VSCodeStableAdapter(VSCodeAdapter):
    tool_name = "VS Code"

    def config_path(self) -> pathlib.Path | None:
        from agent_core.detectors.vscode import VSCodeDetector
        return VSCodeDetector().config_path()


class VSCodeInsidersAdapter(VSCodeAdapter):
    tool_name = "VS Code Insiders"

    def config_path(self) -> pathlib.Path | None:
        from agent_core.detectors.vscode import VSCodeInsidersDetector
        return VSCodeInsidersDetector().config_path()


class VSCodiumAdapter(VSCodeAdapter):
    tool_name = "VSCodium"

    def config_path(self) -> pathlib.Path | None:
        from agent_core.detectors.vscode import VSCodiumDetector
        return VSCodiumDetector().config_path()
