"""
Tool selection tracking and observability.

Tracks which tools are selected/filtered for each query.
Logs to JSONL file for analysis.
"""

import datetime
import json
import logging
import pathlib
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

LOG_FILE = pathlib.Path.home() / ".agent-corex" / "tool_selection_logs.jsonl"


class ToolSelectionTracker:
    """Track tool selections and filtering decisions."""

    def __init__(self):
        self._log_path = LOG_FILE

    def _ensure_dir(self) -> None:
        """Ensure log directory exists."""
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def track(
        self,
        query: str,
        selected_tools: List[str],
        rejected_tools: List[str],
        scores: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Track a tool selection event.

        Args:
            query: The user query that triggered tool selection
            selected_tools: List of tool names that were selected
            rejected_tools: List of tool names that were filtered out
            scores: Scoring details (e.g., keyword scores, embedding similarities)
        """
        self._ensure_dir()

        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "query": query,
            "selected_tools": selected_tools,
            "rejected_tools": rejected_tools,
            "selected_count": len(selected_tools),
            "rejected_count": len(rejected_tools),
        }

        if scores:
            entry["scores"] = scores

        # Write to JSONL file
        try:
            with open(self._log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            logger.debug(
                "Tracked tool selection: query=%r, selected=%d, rejected=%d",
                query,
                len(selected_tools),
                len(rejected_tools),
            )
        except Exception as e:
            logger.error("Failed to write to tool selection log: %s", e)


# Module-level singleton
_tracker: Optional[ToolSelectionTracker] = None


def get_tracker() -> ToolSelectionTracker:
    """Get or create the module-level ToolSelectionTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = ToolSelectionTracker()
    return _tracker
