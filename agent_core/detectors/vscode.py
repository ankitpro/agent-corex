"""
Detectors for VS Code variants' MCP configuration.

VS Code (1.99+) stores MCP servers in the user-level settings.json:

    {
      "mcp": {
        "servers": {
          "agent-corex": {
            "type": "stdio",
            "command": "agent-corex",
            "args": ["serve"]
          }
        }
      }
    }

Three variants are detected:
  - VS Code Stable   (Code)
  - VS Code Insiders (Code - Insiders)
  - VSCodium         (VSCodium)
"""

from __future__ import annotations

import os
import pathlib
import sys

from agent_core.detectors.base import BaseDetector


def _appdata() -> pathlib.Path | None:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        return pathlib.Path(appdata) if appdata else None
    if sys.platform == "darwin":
        return pathlib.Path.home() / "Library" / "Application Support"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return pathlib.Path(xdg) if xdg else pathlib.Path.home() / ".config"


class VSCodeDetector(BaseDetector):
    """VS Code Stable — settings.json is the MCP config target."""

    name = "VS Code"
    _folder = "Code"

    def config_path(self) -> pathlib.Path | None:
        base = _appdata()
        if base is None:
            return None
        return base / self._folder / "User" / "settings.json"


class VSCodeInsidersDetector(VSCodeDetector):
    """VS Code Insiders."""

    name = "VS Code Insiders"
    _folder = "Code - Insiders"


class VSCodiumDetector(VSCodeDetector):
    """VSCodium (open-source VS Code fork)."""

    name = "VSCodium"
    _folder = "VSCodium"
