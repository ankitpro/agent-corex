"""
Executor — execute tasks and generate tool plans via the Agent-CoreX API.

API endpoints used:

  GET  /retrieve_tools?query=<task>&top_k=<n>  → ranked list of relevant tools
  POST /execute_tool                           → execute a specific tool

Typical flow for ``execute_task``:
  1. GET /retrieve_tools → select best tool
  2. POST /execute_tool  → run it and return the result

Typical flow for ``get_tool_plan``:
  1. GET /retrieve_tools → return ordered list as a human-readable plan

Both functions honour AGENT_COREX_API_KEY and the JWT session stored in
~/.agent-corex/config.json.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx

from agent_core import local_config


class Executor:
    """Execute tasks and generate plans using the Agent-CoreX backend."""

    DEFAULT_TOP_K: int = 5

    def __init__(self, base_url: Optional[str] = None) -> None:
        """
        Args:
            base_url: Override the API base URL (default: from local_config).
        """
        self._base_url = (base_url or local_config.get_base_url()).rstrip("/")

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _auth_headers(self) -> Dict[str, str]:
        """Return Authorization headers, checking ENV var first."""
        key = os.getenv("AGENT_COREX_API_KEY") or local_config.get_api_key()
        if key:
            return {"Authorization": f"Bearer {key}"}
        token = local_config.get_access_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    _KEYS_URL = "https://www.agent-corex.com/dashboard/keys"

    def _require_auth(self) -> None:
        """Raise PermissionError if no credentials are available."""
        if not self._auth_headers():
            raise PermissionError(
                "Authentication required.\n"
                f"  Get your API key : {self._KEYS_URL}\n"
                "  Then run         : uvx agent-corex login --key <key>\n"
                "  Or set env var   : AGENT_COREX_API_KEY=acx_..."
            )

    # ── Tool retrieval ────────────────────────────────────────────────────────

    def retrieve_tools(self, task: str, top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant tools for a natural-language task.

        GET /retrieve_tools?query=<task>&top_k=<top_k>

        Args:
            task:  Natural-language description of what needs to be done.
            top_k: Maximum number of tools to return.

        Returns:
            List of tool dicts ordered by relevance::

                [
                  {
                    "name": "summarize_video",
                    "description": "...",
                    "server": "youtube",
                    "score": 0.92
                  },
                  ...
                ]

        Raises:
            PermissionError: Not authenticated.
            RuntimeError:    Network or API error.
        """
        self._require_auth()
        url = f"{self._base_url}/retrieve_tools"
        params = {"query": task, "top_k": top_k}

        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.get(url, params=params, headers=self._auth_headers())
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Cannot reach Agent-CoreX backend at {self._base_url}. "
                "Check your internet connection."
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"Request timed out retrieving tools for task.") from exc

        if resp.status_code == 401:
            raise PermissionError("Authentication failed. Run:  uvx agent-corex login")
        if resp.status_code != 200:
            raise RuntimeError(f"API error {resp.status_code} retrieving tools: {resp.text}")

        data = resp.json()
        # The endpoint may return {"tools": [...]} or a bare list
        if isinstance(data, list):
            return data
        return data.get("tools", data.get("results", []))

    # ── Task execution ────────────────────────────────────────────────────────

    def execute_task(
        self,
        task: str,
        tool_name: Optional[str] = None,
        arguments: Optional[Dict[str, Any]] = None,
        top_k: int = DEFAULT_TOP_K,
    ) -> Dict[str, Any]:
        """
        Execute a task via the Agent-CoreX backend.

        Steps:
          1. If ``tool_name`` is not provided, retrieve the best tool for the task.
          2. POST /execute_tool with the selected tool and arguments.

        Args:
            task:      Natural-language task description.
            tool_name: Specific tool to use.  Auto-selected if omitted.
            arguments: Tool input arguments.  ``{"task": task}`` if omitted.
            top_k:     Candidate pool size when auto-selecting a tool.

        Returns:
            Execution result dict::

                {
                  "tool":    "summarize_video",
                  "result":  "The video discusses ...",
                  "status":  "success"
                }

        Raises:
            PermissionError: Not authenticated.
            RuntimeError:    Network, API, or execution error.
        """
        self._require_auth()

        # Auto-select tool if not specified
        if not tool_name:
            tools = self.retrieve_tools(task, top_k=top_k)
            if not tools:
                raise RuntimeError(
                    f"No tools found for task: '{task}'.\n"
                    "Try  uvx agent-corex retrieve '<task>'  to debug."
                )
            tool_name = tools[0]["name"]

        payload = {
            "tool_name": tool_name,
            "arguments": arguments or {"task": task},
        }

        url = f"{self._base_url}/execute_tool"
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(url, json=payload, headers=self._auth_headers())
        except httpx.ConnectError as exc:
            raise RuntimeError(f"Cannot reach Agent-CoreX backend at {self._base_url}.") from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(f"Execution timed out for tool '{tool_name}'.") from exc

        if resp.status_code == 401:
            raise PermissionError("Authentication failed. Run:  uvx agent-corex login")
        if resp.status_code == 404:
            raise RuntimeError(
                f"Tool '{tool_name}' not found on backend. "
                "It may require a pack to be installed."
            )
        if resp.status_code != 200:
            raise RuntimeError(
                f"API error {resp.status_code} executing tool '{tool_name}': {resp.text}"
            )

        result = resp.json()
        return {
            "tool": tool_name,
            "result": result.get("result", result.get("output", result)),
            "status": result.get("status", "success"),
        }

    # ── Plan generation ───────────────────────────────────────────────────────

    def get_tool_plan(self, task: str, top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        """
        Generate an ordered tool execution plan for a task without running anything.

        Steps:
          1. GET /retrieve_tools to rank relevant tools.
          2. Return a structured plan with reasoning for each step.

        Args:
            task:  Natural-language task description.
            top_k: Number of candidate tools to consider.

        Returns:
            Plan dict::

                {
                  "task":  "summarize the latest video on the channel",
                  "steps": [
                    {
                      "step":        1,
                      "tool":        "list_channel_videos",
                      "description": "...",
                      "server":      "youtube",
                      "score":       0.94
                    },
                    ...
                  ],
                  "tool_count": 3
                }

        Raises:
            PermissionError: Not authenticated.
            RuntimeError:    Network or API error.
        """
        self._require_auth()
        tools = self.retrieve_tools(task, top_k=top_k)

        if not tools:
            return {
                "task": task,
                "steps": [],
                "tool_count": 0,
                "note": "No relevant tools found. Install more packs to expand coverage.",
            }

        steps = [
            {
                "step": i + 1,
                "tool": t.get("name", f"tool_{i + 1}"),
                "description": t.get("description", ""),
                "server": t.get("server", ""),
                "score": round(float(t.get("score", 0)), 4),
            }
            for i, t in enumerate(tools)
        ]

        return {
            "task": task,
            "steps": steps,
            "tool_count": len(steps),
        }
