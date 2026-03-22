"""Detector for Cursor's MCP configuration file."""

import os
import pathlib
import sys

from agent_core.detectors.base import BaseDetector


def _appdata() -> pathlib.Path | None:
    """Return the OS-specific application data directory."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        return pathlib.Path(appdata) if appdata else None
    if sys.platform == "darwin":
        return pathlib.Path.home() / "Library" / "Application Support"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return pathlib.Path(xdg) if xdg else pathlib.Path.home() / ".config"


class CursorDetector(BaseDetector):
    name = "Cursor"

    def config_path(self) -> pathlib.Path | None:
        base = _appdata()
        if base is None:
            return None
        return base / "Cursor" / "User" / "mcp.json"
