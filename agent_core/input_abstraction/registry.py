"""Thread-safe registry for abstracted tool input schemas.

Supports:
  - Lazy generation from raw MCP schemas via classifier
  - Manual overrides for tools that need tuning
  - Cache invalidation on tool discovery
"""

from __future__ import annotations

import threading
from typing import Optional

from .classifier import ParamClassifier
from .models import ToolInputSchema


class AbstractionRegistry:
    """Thread-safe registry of ToolInputSchema for tools.

    Two-layer lookup:
      1. Custom overrides (highest priority) — manually defined schemas
      2. Auto-generated cache — built on-demand from raw MCP inputSchema
    """

    def __init__(self, classifier: Optional[ParamClassifier] = None) -> None:
        """Initialize the registry.

        Args:
            classifier: ParamClassifier for auto-generation. If None, creates a new one.
        """
        self._classifier = classifier or ParamClassifier()
        self._cache: dict[str, ToolInputSchema] = {}
        self._overrides: dict[str, ToolInputSchema] = {}
        self._lock = threading.Lock()

    def get(self, tool_name: str, server: str, raw_schema: dict) -> ToolInputSchema:
        """Get or generate the abstracted schema for a tool.

        Lookup order:
          1. Manual overrides
          2. Cache (auto-generated)
          3. Generate on-demand via classifier

        Args:
            tool_name: Name of the tool
            server: MCP server name
            raw_schema: Raw inputSchema from MCP

        Returns:
            ToolInputSchema with required/optional/internal classified
        """
        with self._lock:
            # Check overrides first
            if tool_name in self._overrides:
                return self._overrides[tool_name]

            # Check cache
            if tool_name in self._cache:
                return self._cache[tool_name]

            # Generate on-demand
            schema = self._classifier.build_schema(tool_name, server, raw_schema)
            self._cache[tool_name] = schema
            return schema

    def register_override(self, schema: ToolInputSchema) -> None:
        """Register a manually-crafted schema override for a tool.

        Use this when the auto-classifier gets a tool wrong.

        Args:
            schema: ToolInputSchema with is_auto_generated=False
        """
        with self._lock:
            self._overrides[schema.tool_name] = schema

    def invalidate(self, tool_name: Optional[str] = None) -> None:
        """Invalidate cache entries (called when MCP discovery refreshes tools).

        Args:
            tool_name: Specific tool to invalidate. If None, clears entire cache.
        """
        with self._lock:
            if tool_name is not None:
                self._cache.pop(tool_name, None)
            else:
                self._cache.clear()

    def get_cache_size(self) -> int:
        """Return size of auto-generated cache (for diagnostics)."""
        with self._lock:
            return len(self._cache)

    def get_override_count(self) -> int:
        """Return count of manual overrides (for diagnostics)."""
        with self._lock:
            return len(self._overrides)
