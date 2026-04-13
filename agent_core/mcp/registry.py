"""
MCPRegistry — bundled catalog of known MCP servers.

Loaded from mcp_registry.json which ships with the package.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_REGISTRY_FILE = Path(__file__).parent / "mcp_registry.json"


class MCPRegistry:
    """Static catalog of known MCP servers. Ships with the package."""

    def __init__(self) -> None:
        self._servers: List[Dict] = []
        self._by_name: Dict[str, Dict] = {}
        self._load()

    def _load(self) -> None:
        if _REGISTRY_FILE.exists():
            with open(_REGISTRY_FILE, encoding="utf-8") as f:
                self._servers = json.load(f)
            self._by_name = {s["name"]: s for s in self._servers}

    def list_all(self) -> List[Dict]:
        """Return all active server entries."""
        return [s for s in self._servers if s.get("is_active", True)]

    def get(self, name: str) -> Optional[Dict]:
        """Return a server entry by name, or None if not found."""
        return self._by_name.get(name)

    def to_mcp_config_entry(self, name: str, env_overrides: dict | None = None) -> Optional[Dict]:
        """Convert a registry entry to ~/.agent-corex/mcp.json format."""
        entry = self.get(name)
        if not entry:
            return None
        cfg: Dict = {
            "command": entry["command"],
            "args": entry["args"],
        }
        if env_overrides:
            cfg["env"] = env_overrides
        return cfg
