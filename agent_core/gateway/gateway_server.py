"""
Agent-CoreX MCP stdio server.

Exposes THREE tools:
  execute_query(query: str)                        → end-to-end task execution
  discover_capabilities(query?: str)               → what can I do with installed servers?
  search_tools(query: str, top_k?: int)            → find specific tools

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
    },
    {
        "name": "discover_capabilities",
        "description": (
            "Discover what the user can do with their installed MCP servers. "
            "Returns capabilities grouped by server with examples. "
            "If no servers are installed, returns recommended servers to install instead. "
            "Call this before execute_query when you want to know what's available."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional hint about the domain you're interested in (e.g. 'deploy', 'database'). Omit for a general overview.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "search_tools",
        "description": (
            "Search for specific tools available across the user's installed MCP servers. "
            "Returns matching tools filtered to only the user's servers. "
            "If no servers are installed, returns server recommendations with relevant examples. "
            "Use this to find the right tool before calling execute_query."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What you want to do (e.g. 'list projects', 'send email', 'deploy service').",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Maximum number of tools to return (default 5, max 20).",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
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


def _make_client() -> AgentCoreXClient:
    return AgentCoreXClient(
        api_url=local_config.get_api_url(),
        api_key=local_config.get_api_key(),
    )


def _tool_result(id_: Any, text: str, is_error: bool = False) -> dict:
    return _ok(id_, {"content": [{"type": "text", "text": text}], "isError": is_error})


def _handle_execute_query(id_: Any, arguments: dict) -> dict:
    query = arguments.get("query", "").strip()
    if not query:
        return _tool_result(id_, "Error: 'query' argument is required.", is_error=True)
    try:
        response = _make_client().execute_query(query)
        return _tool_result(id_, _format_response(response))
    except AuthError as exc:
        return _tool_result(id_, f"Authentication error: {exc}", is_error=True)
    except ConnectionError as exc:
        return _tool_result(id_, f"Cannot reach Agent-CoreX backend: {exc}", is_error=True)
    except (TimeoutError, AgentCoreXError, Exception) as exc:
        return _tool_result(id_, f"Error: {exc}", is_error=True)


def _handle_discover_capabilities(id_: Any, arguments: dict) -> dict:
    query: Optional[str] = arguments.get("query") or None
    try:
        result = _make_client().discover_capabilities(query=query)
    except AuthError as exc:
        return _tool_result(id_, f"Authentication error: {exc}", is_error=True)
    except ConnectionError as exc:
        return _tool_result(id_, f"Cannot reach Agent-CoreX backend: {exc}", is_error=True)
    except (TimeoutError, AgentCoreXError, Exception) as exc:
        return _tool_result(id_, f"Error: {exc}", is_error=True)

    lines: list[str] = []
    capabilities = result.get("capabilities", [])
    recommendations = result.get("recommended_servers", [])
    message = result.get("message")

    if capabilities:
        for cap in capabilities:
            lines.append(f"## {cap.get('title', cap.get('server', ''))}")
            lines.append(f"Server: {cap.get('server', '')}")
            for ex in cap.get("examples", []):
                lines.append(f"  - {ex}")
            lines.append("")
    elif recommendations:
        if message:
            lines.append(message)
            lines.append("")
        lines.append("Recommended servers to install:")
        for rec in recommendations:
            lines.append(f"\n### {rec.get('name', '')}")
            lines.append(rec.get("reason", ""))
            for ex in rec.get("examples", []):
                lines.append(f"  - {ex}")
            lines.append(f"  Install: agent-corex mcp add {rec.get('name', '')}")
    else:
        lines.append("No capabilities found. Install a server first: agent-corex mcp add <server>")

    return _tool_result(id_, "\n".join(lines))


def _handle_search_tools(id_: Any, arguments: dict) -> dict:
    query = arguments.get("query", "").strip()
    if not query:
        return _tool_result(id_, "Error: 'query' argument is required.", is_error=True)
    top_k = int(arguments.get("top_k") or 5)
    try:
        result = _make_client().search_tools(query=query, top_k=top_k)
    except AuthError as exc:
        return _tool_result(id_, f"Authentication error: {exc}", is_error=True)
    except ConnectionError as exc:
        return _tool_result(id_, f"Cannot reach Agent-CoreX backend: {exc}", is_error=True)
    except (TimeoutError, AgentCoreXError, Exception) as exc:
        return _tool_result(id_, f"Error: {exc}", is_error=True)

    lines: list[str] = []
    tools = result.get("tools", [])
    recommendations = result.get("recommended_servers", [])

    if tools:
        lines.append(f"Tools matching '{query}':\n")
        for t in tools:
            lines.append(f"- [{t.get('server', '')}] {t.get('name', '')}: {t.get('description', '')}")
    elif recommendations:
        lines.append(f"No installed servers have tools matching '{query}'.\n")
        lines.append("Servers that could help:")
        for rec in recommendations:
            lines.append(f"\n### {rec.get('name', '')}")
            lines.append(rec.get("reason", ""))
            for ex in rec.get("examples", []):
                lines.append(f"  - {ex}")
            lines.append(f"  Install: agent-corex mcp add {rec.get('name', '')}")
    else:
        lines.append(f"No tools found for: {query}")

    return _tool_result(id_, "\n".join(lines))


def _handle_tools_call(id_: Any, params: dict) -> dict:
    name = params.get("name", "")
    arguments = params.get("arguments") or {}

    if name == "execute_query":
        return _handle_execute_query(id_, arguments)
    if name == "discover_capabilities":
        return _handle_discover_capabilities(id_, arguments)
    if name == "search_tools":
        return _handle_search_tools(id_, arguments)

    return _err(id_, -32601, f"Unknown tool: {name!r}")


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
