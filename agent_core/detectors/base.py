"""Abstract base class for MCP-client detectors."""

import pathlib
from abc import ABC, abstractmethod


class BaseDetector(ABC):
    """
    Checks whether a particular AI tool (Claude Desktop, Cursor, …)
    is installed and locates its MCP configuration file.
    """

    name: str = ""

    @abstractmethod
    def config_path(self) -> pathlib.Path | None:
        """Return the absolute path to the tool's MCP config file, or None."""

    def is_installed(self) -> bool:
        """Return True if the config file exists on disk."""
        p = self.config_path()
        return p is not None and p.exists()

    def summary(self) -> dict:
        p = self.config_path()
        return {
            "tool": self.name,
            "installed": self.is_installed(),
            "config_path": str(p) if p else None,
        }
