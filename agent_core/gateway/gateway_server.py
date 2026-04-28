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
from agent_core import capabilities as _capabilities
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

# Module-level capability payload cache. Populated lazily on first use
# (initialize / tools/list / prompts / resources) and refreshed only when
# `invalidate_capability_cache()` is called — the CLI invalidates on every
# `mcp add` / `mcp remove` so the process restart path picks up fresh data.
_capability_payload: Optional[dict] = None


def _get_capability_payload() -> dict:
    """Fetch capabilities once and memoize. Never raises."""
    global _capability_payload
    if _capability_payload is not None:
        return _capability_payload
    try:
        _capability_payload = _capabilities.fetch(_make_client())
    except Exception:
        _capability_payload = {
            "servers": {},
            "skills": [],
            "templates": [],
            "installed_servers": [],
        }
    return _capability_payload


def invalidate_capability_cache() -> None:
    """Clear in-process + on-disk capability caches. Used by tests."""
    global _capability_payload
    _capability_payload = None
    _capabilities.invalidate()


BASE_TOOLS = [
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

# Backwards-compat alias: older tests / imports expect `TOOLS`. The runtime
# always goes through `_build_dynamic_tools(payload)` for tools/list.
TOOLS = BASE_TOOLS


def _build_dynamic_tools(payload: dict) -> list[dict]:
    """
    Clone BASE_TOOLS and rewrite descriptions to enumerate installed servers
    and steer the LLM toward execute_query over built-in shell tools.

    MCP hosts (Claude Desktop, Cursor, VS Code) surface tool descriptions to
    the model at every turn — this is the channel that actually drives
    routing. The instructions/prompts fields are unreliable across hosts.
    """
    tools = [dict(t) for t in BASE_TOOLS]
    servers: dict = payload.get("servers") or {}
    installed = payload.get("installed_servers") or list(servers.keys())

    if not installed:
        return tools

    server_list = ", ".join(installed)

    # Collect up to 6 concrete example phrases across all installed servers
    examples: list[str] = []
    for block in servers.values():
        for cap in (block or {}).get("capabilities", []):
            for ex in cap.get("examples", []):
                if ex and ex not in examples:
                    examples.append(ex)
                    if len(examples) >= 6:
                        break
            if len(examples) >= 6:
                break
        if len(examples) >= 6:
            break

    # Add template patterns as high-confidence example phrasings
    for tmpl in (payload.get("templates") or [])[:6]:
        pattern = tmpl.get("pattern")
        if pattern and pattern not in examples:
            examples.append(pattern)

    example_block = ""
    if examples:
        example_block = " Examples: " + "; ".join(f'"{e}"' for e in examples[:8]) + "."

    for tool in tools:
        if tool["name"] == "execute_query":
            tool["description"] = (
                f"Execute tasks against the user's installed MCP servers "
                f"({server_list}) via Agent-CoreX. "
                f"ALWAYS prefer this tool over running shell commands, CLI invocations, "
                f"or Bash when the task touches any of: {server_list}. "
                f"Send a natural-language query; tool selection, input resolution, and "
                f"execution are handled automatically by the backend."
                f"{example_block}"
            )
        elif tool["name"] == "discover_capabilities":
            tool["description"] = (
                f"Show what the user can do with their installed MCP servers "
                f"({server_list}). Returns capabilities grouped by server with "
                f"example phrasings. Call this first if unsure which server or "
                f"tool applies to the current task."
            )
        elif tool["name"] == "search_tools":
            tool["description"] = (
                f"Search for tools across the user's installed MCP servers "
                f"({server_list}). Use this to locate the right tool before "
                f"calling execute_query when a query is ambiguous."
            )
    return tools


# ── Response helpers ──────────────────────────────────────────────────────────


def _ok(id_: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}}


def _write(obj: dict) -> None:
    # ensure_ascii=True escapes every non-ASCII char as \uXXXX. MCP hosts
    # decode either form, and this belt-and-suspenders guarantees we never
    # hit a UnicodeEncodeError if the host's stdout is a legacy codepage
    # (e.g. Windows cp1252) and `_force_utf8_stdio` didn't get to run.
    line = json.dumps(obj, ensure_ascii=True)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


# ── Response formatter ────────────────────────────────────────────────────────


def _stringify_preview(result: Any) -> str:
    """Convert a raw MCP tool result to a short preview string."""
    if isinstance(result, str):
        return result[:300]
    if isinstance(result, list):
        if not result:
            return ""
        # Extract text content from MCP content blocks
        texts = []
        for item in result:
            if isinstance(item, dict) and item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif isinstance(item, str):
                texts.append(item)
        return " ".join(texts)[:300] if texts else str(result)[:300]
    if isinstance(result, dict):
        if "error" in result:
            return result.get("error", "error")[:300]
        # Try to extract a text field
        for key in ("text", "content", "output", "result", "data"):
            if key in result:
                return str(result[key])[:300]
        return str(result)[:300]
    return str(result)[:300] if result else ""


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
    """
    Advertise tools + prompts + resources so MCP hosts will query all three.

    `instructions` is still sent for hosts that honor it, but the real
    steering happens via dynamic tool descriptions in tools/list — that is
    the channel every host surfaces to the model at every turn.
    """
    result = {
        "protocolVersion": PROTOCOL_VERSION,
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        "capabilities": {
            "tools": {},
            "prompts": {},
            "resources": {},
        },
    }
    payload = _get_capability_payload()
    block = _capabilities.build_system_block(payload)
    if block:
        result["instructions"] = block
    return _ok(id_, result)


def _handle_tools_list(id_: Any, _params: dict) -> dict:
    payload = _get_capability_payload()
    return _ok(id_, {"tools": _build_dynamic_tools(payload)})


# ── prompts/* ────────────────────────────────────────────────────────────────

_PROMPT_NAME = "agent_corex_capabilities"


def _handle_prompts_list(id_: Any, _params: dict) -> dict:
    return _ok(
        id_,
        {
            "prompts": [
                {
                    "name": _PROMPT_NAME,
                    "description": (
                        "Load the current Agent-CoreX capability context "
                        "(installed MCP servers, their tools, and example "
                        "phrasings). Invoke this prompt to steer the model "
                        "toward agent-corex for tasks matching the installed "
                        "servers."
                    ),
                    "arguments": [],
                }
            ]
        },
    )


def _handle_prompts_get(id_: Any, params: dict) -> dict:
    name = params.get("name", "")
    if name != _PROMPT_NAME:
        return _err(id_, -32602, f"Unknown prompt: {name!r}")
    payload = _get_capability_payload()
    block = _capabilities.build_system_block(payload) or (
        "No MCP servers installed. Run `agent-corex mcp add <server>` first."
    )
    return _ok(
        id_,
        {
            "description": "Agent-CoreX installed capabilities",
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": block},
                }
            ],
        },
    )


# ── resources/* ──────────────────────────────────────────────────────────────

_CAPABILITIES_URI = "agent-corex://capabilities"


def _handle_resources_list(id_: Any, _params: dict) -> dict:
    return _ok(
        id_,
        {
            "resources": [
                {
                    "uri": _CAPABILITIES_URI,
                    "name": "Agent-CoreX capabilities",
                    "description": (
                        "Structured JSON of installed MCP servers, their "
                        "tools, skills, and query templates. Read this to "
                        "decide which tools apply to a given task."
                    ),
                    "mimeType": "application/json",
                }
            ]
        },
    )


def _handle_resources_read(id_: Any, params: dict) -> dict:
    uri = params.get("uri", "")
    if uri != _CAPABILITIES_URI:
        return _err(id_, -32602, f"Unknown resource: {uri!r}")
    payload = _get_capability_payload()
    return _ok(
        id_,
        {
            "contents": [
                {
                    "uri": _CAPABILITIES_URI,
                    "mimeType": "application/json",
                    "text": json.dumps(payload, ensure_ascii=False, indent=2),
                }
            ]
        },
    )


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

    client = _make_client()

    # Get plan from backend (free-tier: backend plans, client executes locally with stored credentials)
    try:
        plan = client.plan_query(query)
    except AuthError as exc:
        return _tool_result(id_, f"Authentication error: {exc}", is_error=True)
    except ConnectionError as exc:
        return _tool_result(id_, f"Cannot reach Agent-CoreX backend: {exc}", is_error=True)
    except (TimeoutError, AgentCoreXError, Exception) as exc:
        return _tool_result(id_, f"Error: {exc}", is_error=True)

    # Execute each planned step locally using MCPManager (loads env from ~/.agent-corex/mcp.json)
    from agent_core.mcp.manager import MCPManager
    import time

    mgr = MCPManager.from_local_store()
    steps = plan.get("steps", [])
    executed_steps = []

    for i, step in enumerate(steps):
        # Skip steps that need input or were already skipped
        if step.get("needs_input") or step.get("skipped"):
            executed_steps.append(step)
            continue

        server = step.get("server") or ""
        tool = step.get("tool") or ""
        inputs = step.get("inputs") or {}

        if not server or not tool:
            step = dict(step)
            step["success"] = False
            step["error"] = "no_tool_planned"
            executed_steps.append(step)
            continue

        step = dict(step)  # Don't modify the original step
        t0 = time.monotonic()
        try:
            # Execute the tool locally with the user's stored env vars
            raw_result = mgr.call_tool(server, tool, inputs)
            latency_ms = int((time.monotonic() - t0) * 1000)
            step["latency_ms"] = latency_ms

            # Report result back to backend for state management
            try:
                ref_data = client.submit_result(
                    {
                        "server": server,
                        "tool": tool,
                        "inputs": inputs,
                        "output": raw_result,
                        "success": True,
                        "step_index": i,
                        "latency_ms": latency_ms,
                    }
                )
                step["success"] = True
                step["ref"] = ref_data.get("ref")
                step["preview"] = ref_data.get("preview") or _stringify_preview(raw_result)
            except Exception:
                # If submit_result fails, still report local execution succeeded
                step["success"] = True
                step["preview"] = _stringify_preview(raw_result)
        except ValueError as exc:
            # Server not in local store
            step["success"] = False
            step["error"] = str(exc)
        except Exception as exc:
            step["success"] = False
            step["error"] = f"execution_failed: {exc}"

        executed_steps.append(step)

    mgr.shutdown_all()

    return _tool_result(
        id_,
        _format_response(
            {
                "steps": executed_steps,
                "total_latency_ms": plan.get("total_latency_ms", 0),
            }
        ),
    )


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
            lines.append(
                f"- [{t.get('server', '')}] {t.get('name', '')}: {t.get('description', '')}"
            )
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
    if method == "prompts/list":
        return _handle_prompts_list(id_, params)
    if method == "prompts/get":
        return _handle_prompts_get(id_, params)
    if method == "resources/list":
        return _handle_resources_list(id_, params)
    if method == "resources/read":
        return _handle_resources_read(id_, params)
    if method == "ping":
        return _ok(id_, {})

    # Unknown method
    if id_ is not None:
        return _err(id_, -32601, f"Method not found: {method!r}")
    return None


def _force_utf8_stdio() -> None:
    """
    Force stdin/stdout to UTF-8 so the gateway can emit any JSON payload
    regardless of the host OS default encoding.

    On Windows, Python defaults stdout to cp1252, which cannot encode common
    characters like '→' or any non-Latin script — an MCP host parsing the
    broken response would disconnect the server. `reconfigure()` is a no-op
    on streams that are already UTF-8.
    """
    for stream in (sys.stdout, sys.stdin, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def run() -> None:
    """Enter the MCP stdio read loop. Runs until stdin closes."""
    _force_utf8_stdio()
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
