"""Adapter for Cursor's mcp.json."""

from __future__ import annotations

import pathlib

from agent_core.config_adapters.base import BaseAdapter
from agent_core.detectors.cursor import CursorDetector


class CursorAdapter(BaseAdapter):
    tool_name = "Cursor"

    def config_path(self) -> pathlib.Path | None:
        return CursorDetector().config_path()
