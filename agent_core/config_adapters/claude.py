"""Adapter for Claude Desktop's claude_desktop_config.json."""

import pathlib

from agent_core.config_adapters.base import BaseAdapter
from agent_core.detectors.claude import ClaudeDesktopDetector


class ClaudeAdapter(BaseAdapter):
    tool_name = "Claude Desktop"

    def config_path(self) -> pathlib.Path | None:
        return ClaudeDesktopDetector().config_path()


from __future__ import annotations
