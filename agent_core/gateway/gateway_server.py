"""
MCP Gateway Server — stdio-based JSON-RPC 2.0 server.

This is the process that Claude Desktop / Cursor launch when they see:
  {
    "agent-corex": {
      "command": "agent-corex",
      "args": ["serve"]
    }
  }

Protocol:
  1. Claude sends  initialize   → we respond with server capabilities
  2. Claude sends  tools/list   → we return ALL tools (free + enterprise)
  3. Claude sends  tools/call   → we route the call:
       free tool      → execute locally
       enterprise     → check API key first; return error if not authenticated

Run:
  agent-corex serve
  python -m agent_core.gateway.gateway_server
"""

from __future__ import annotations

import json
import pathlib
import sys
import traceback
from typing import Any

from agent_core.gateway.tool_router import ToolRouter
from agent_core.gateway.auth_middleware import check_auth

SERVER_NAME = "agent-corex"
SERVER_VERSION = "1.0.3"
PROTOCOL_VERSION = "2024-11-05"


def _send(obj: dict) -> None:
    """Write a JSON-RPC message to stdout and flush."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _error_response(req_id: Any, code: int, message: str, data: Any = None) -> dict:
    err: dict = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


def _ok_response(req_id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


# ---------------------------------------------------------------------------
# Handler implementations
# ---------------------------------------------------------------------------

def _handle_initialize(req_id: Any, _params: dict, router: ToolRouter) -> dict:
    return _ok_response(req_id, {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {
            "tools": {"listChanged": False},
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    })


def _handle_tools_list(req_id: Any, _params: dict, router: ToolRouter) -> dict:
    return _ok_response(req_id, {"tools": router.tools_list()})


def _handle_tools_call(req_id: Any, params: dict, router: ToolRouter) -> dict:
    tool_name: str = params.get("name", "")
    arguments: dict = params.get("arguments") or {}

    meta = router.get_meta(tool_name)
    if meta is None:
        return _error_response(req_id, -32602, f"Unknown tool: {tool_name!r}")

    # ── Enterprise gate ────────────────────────────────────────────────────
    if router.is_enterprise(tool_name):
        auth_err = check_auth()
        if auth_err is not None:
            # Return a structured tool result with the auth error — do NOT crash
            return _ok_response(req_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(auth_err, indent=2),
                    }
                ],
                "isError": True,
            })

        # Auth passed — enterprise execution (stub: real backend call goes here)
        result_text = (
            f"[Enterprise tool: {tool_name}]\n"
            f"Arguments: {json.dumps(arguments, indent=2)}\n\n"
            "This tool requires a running enterprise backend.\n"
            "See: https://agent-corex.ai/docs/enterprise"
        )
        return _ok_response(req_id, {
            "content": [{"type": "text", "text": result_text}]
        })

    # ── Free tool execution ────────────────────────────────────────────────
    try:
        result = router.execute_free_tool(tool_name, arguments)
        text = result if isinstance(result, str) else json.dumps(result, indent=2)
        return _ok_response(req_id, {
            "content": [{"type": "text", "text": text}]
        })
    except Exception as exc:
        return _ok_response(req_id, {
            "content": [{"type": "text", "text": f"Tool execution error: {exc}"}],
            "isError": True,
        })


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def run() -> None:
    """
    Start the MCP gateway server.
    Reads JSON-RPC requests from stdin, writes responses to stdout.
    Runs until stdin is closed.
    """
    # Load local MCP tools from ~/.agent-corex/mcp.json if available
    extra_tools = []
    local_mcp_config = pathlib.Path.home() / ".agent-corex" / "mcp.json"
    if local_mcp_config.exists():
        try:
            from agent_core.tools.mcp.mcp_loader import MCPLoader

            loader = MCPLoader(str(local_mcp_config))
            manager = loader.load()
            extra_tools = manager.get_all_tools()
            print(
                f"Loaded {len(extra_tools)} tools from local MCP config",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"Warning: Could not load local MCP tools: {e}", file=sys.stderr)

    router = ToolRouter(extra_tools=extra_tools)

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        try:
            msg = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            _send(_error_response(None, -32700, f"Parse error: {exc}"))
            continue

        req_id = msg.get("id")
        method: str = msg.get("method", "")
        params: dict = msg.get("params") or {}

        # Notifications (no id) — acknowledge silently
        if req_id is None:
            continue

        try:
            if method == "initialize":
                response = _handle_initialize(req_id, params, router)
            elif method == "tools/list":
                response = _handle_tools_list(req_id, params, router)
            elif method == "tools/call":
                response = _handle_tools_call(req_id, params, router)
            elif method == "ping":
                response = _ok_response(req_id, {})
            else:
                response = _error_response(req_id, -32601, f"Method not found: {method!r}")
        except Exception:
            tb = traceback.format_exc()
            response = _error_response(req_id, -32603, "Internal error", tb)

        _send(response)


if __name__ == "__main__":
    run()
