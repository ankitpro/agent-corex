"""
Agent-CoreX MCP stdio server — single-tool thin wrapper.

Exposes exactly ONE tool:
  execute_query(query: str) → structured result from v2 backend

Invoked by Claude Desktop / Cursor / VS Code via:
  agent-corex serve
  uvx agent-corex serve

Protocol: JSON-RPC 2.0 over stdio (MCP spec 2024-11-05)
"""

from __future__ import annotations

import json
import sys
from typing import Any, Optional

from agent_core import __version__
from agent_core import local_config
from agent_core.client import (
    AgentCoreXClient,
    AgentCoreXError,
    AuthError,
    ConnectionError,
    TimeoutError,
)

SERVER_NAME = "agent-corex"
SERVER_VERSION = __version__
PROTOCOL_VERSION = "2024-11-05"

# The single tool this MCP server exposes.
TOOLS = [
    {
        "name": "execute_query",
        "description": (
            "Execute any task using Agent-CoreX. "
            "Send a natural language query and receive structured results — "
            "tool selection, input resolution, and execution are handled automatically."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language description of the task to execute.",
                }
            },
            "required": ["query"],
        },
    }
]


# ── Response helpers ──────────────────────────────────────────────────────────


def _ok(id_: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _write(obj: dict) -> None:
    line = json.dumps(obj, ensure_ascii=False)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


# ── Response formatter ────────────────────────────────────────────────────────


def _format_response(response: dict) -> str:
    """Convert a QueryResponse dict into readable text for MCP content."""
    steps = response.get("steps", [])
    total_ms = response.get("total_latency_ms", 0)
    lines: list[str] = []

    for i, step in enumerate(steps, 1):
        tool = step.get("tool") or "unknown"
        if step.get("needs_input"):
            missing = ", ".join(step.get("missing_inputs") or [])
            lines.append(f"Step {i}: {tool} [needs input: {missing}]")
        elif step.get("skipped"):
            reason = step.get("skip_reason") or "low confidence"
            lines.append(f"Step {i}: {tool} [skipped — {reason}]")
        elif step.get("success"):
            preview = step.get("preview") or ""
            lines.append(f"Step {i}: {tool} [OK]")
            if preview:
                lines.append(f"  {preview}")
            if step.get("ref"):
                lines.append(f"  ref: {step['ref']}")
        else:
            error = step.get("error") or "execution failed"
            lines.append(f"Step {i}: {tool} [FAILED — {error}]")

    lines.append(f"\nTotal: {len(steps)} step(s), {total_ms}ms")
    return "\n".join(lines)


# ── JSON-RPC handlers ─────────────────────────────────────────────────────────


def _handle_initialize(id_: Any, _params: dict) -> dict:
    return _ok(
        id_,
        {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "capabilities": {"tools": {}},
        },
    )


def _handle_tools_list(id_: Any, _params: dict) -> dict:
    return _ok(id_, {"tools": TOOLS})


def _handle_tools_call(id_: Any, params: dict) -> dict:
    name = params.get("name", "")
    arguments = params.get("arguments") or {}

    if name != "execute_query":
        return _err(id_, -32601, f"Unknown tool: {name!r}")

    query = arguments.get("query", "").strip()
    if not query:
        return _ok(
            id_,
            {
                "content": [{"type": "text", "text": "Error: 'query' argument is required."}],
                "isError": True,
            },
        )

    client = AgentCoreXClient(
        api_url=local_config.get_api_url(),
        api_key=local_config.get_api_key(),
    )

    try:
        response = client.execute_query(query)
        text = _format_response(response)
        return _ok(id_, {"content": [{"type": "text", "text": text}], "isError": False})
    except AuthError as exc:
        return _ok(
            id_,
            {
                "content": [{"type": "text", "text": f"Authentication error: {exc}"}],
                "isError": True,
            },
        )
    except ConnectionError as exc:
        return _ok(
            id_,
            {
                "content": [{"type": "text", "text": f"Cannot reach Agent-CoreX backend: {exc}"}],
                "isError": True,
            },
        )
    except (TimeoutError, AgentCoreXError, Exception) as exc:
        return _ok(
            id_,
            {
                "content": [{"type": "text", "text": f"Error: {exc}"}],
                "isError": True,
            },
        )


# ── Main loop ─────────────────────────────────────────────────────────────────


def _dispatch(message: dict) -> Optional[dict]:
    """Dispatch a JSON-RPC message. Returns response dict, or None for notifications."""
    method = message.get("method", "")
    id_ = message.get("id")  # None means notification — no response expected
    params = message.get("params") or {}

    # Notifications: no response
    if id_ is None and method.startswith("notifications/"):
        return None

    if method == "initialize":
        return _handle_initialize(id_, params)
    if method == "tools/list":
        return _handle_tools_list(id_, params)
    if method == "tools/call":
        return _handle_tools_call(id_, params)
    if method == "ping":
        return _ok(id_, {})

    # Unknown method
    if id_ is not None:
        return _err(id_, -32601, f"Method not found: {method!r}")
    return None


def run() -> None:
    """Enter the MCP stdio read loop. Runs until stdin closes."""
    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            message = json.loads(raw_line)
        except json.JSONDecodeError:
            _write(_err(None, -32700, "Parse error"))
            continue

        try:
            response = _dispatch(message)
        except Exception as exc:
            _write(_err(message.get("id"), -32603, f"Internal error: {exc}"))
            continue

        if response is not None:
            _write(response)
