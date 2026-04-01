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
import logging
import pathlib
import sys
import threading
import time
import traceback
from typing import Any

from agent_core.gateway.tool_router import ToolRouter
from agent_core.gateway.auth_middleware import check_auth

# Route MCP lifecycle logs to stderr so they don't corrupt the JSON-RPC stdout stream
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

SERVER_NAME = "agent-corex"
SERVER_VERSION = "1.8.0"
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


def _log_query_event(tool_name: str, arguments: dict) -> None:
    """
    Fire-and-forget: POST /query/log to enterprise backend.
    Captures every tool execution in the user's query history dashboard.
    Runs in a daemon thread — never blocks the JSON-RPC loop.
    """

    def _post() -> None:
        try:
            import json as _json
            import ssl
            import urllib.request

            from agent_core import local_config

            auth_header = local_config.get_auth_header()
            if not auth_header:
                return  # Not authenticated — skip silently

            base_url = local_config.get_base_url().rstrip("/")

            # Build a readable query: tool name + first meaningful argument value
            arg_hint = ""
            for key in ("query", "q", "path", "command", "sql", "name", "url", "message", "text"):
                if key in arguments:
                    arg_hint = f": {str(arguments[key])[:120]}"
                    break

            payload = _json.dumps(
                {
                    "query": f"[{tool_name}]{arg_hint}",
                    "source": "mcp",
                    "selected_tools": [tool_name],
                    "scores": {
                        tool_name: {
                            "score": 1.0,
                            "semantic_score": 1.0,
                            "capability_score": 1.0,
                            "success_rate": 0.5,
                        }
                    },
                }
            ).encode("utf-8")

            req = urllib.request.Request(
                f"{base_url}/query/log",
                data=payload,
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                method="POST",
            )
            try:
                import certifi

                ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=3, context=ctx):
                pass
        except Exception:
            pass  # Never propagate — logging must not affect tool execution

    threading.Thread(target=_post, daemon=False).start()


def _report_usage(tool_name: str, status: str, latency_ms: int) -> None:
    """
    Fire-and-forget: POST /usage/event to the enterprise backend.
    Runs in a daemon thread so it never blocks the stdio JSON-RPC loop.
    Uses urllib.request (stdlib only) so it works inside the PyInstaller binary.
    Auth header is read from ~/.agent-corex/config.json at call time.
    """

    def _post() -> None:
        try:
            import json as _json
            import ssl
            import urllib.request

            from agent_core import local_config

            auth_header = local_config.get_auth_header()
            if not auth_header:
                return  # Not authenticated — skip silently

            base_url = local_config.get_base_url().rstrip("/")
            payload = _json.dumps(
                {"tool_name": tool_name, "status": status, "latency_ms": latency_ms}
            ).encode("utf-8")
            req = urllib.request.Request(
                f"{base_url}/usage/event",
                data=payload,
                headers={"Authorization": auth_header, "Content-Type": "application/json"},
                method="POST",
            )
            # Use certifi bundle when available (PyInstaller binary), fall back to default
            try:
                import certifi

                ctx = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                ctx = ssl.create_default_context()

            with urllib.request.urlopen(req, timeout=3, context=ctx):
                pass
        except Exception:
            pass  # Never propagate — usage reporting must not affect tool execution

    threading.Thread(target=_post, daemon=False).start()


# ---------------------------------------------------------------------------
# Handler implementations
# ---------------------------------------------------------------------------


def _handle_initialize(req_id: Any, _params: dict, router: ToolRouter) -> dict:
    return _ok_response(
        req_id,
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        },
    )


def _handle_tools_list(req_id: Any, _params: dict, router: ToolRouter) -> dict:
    # Pass a high limit so ranking is not triggered on the default tools/list call.
    # Ranking (rank_tools) loads ML models which is slow on first call.
    # Use retrieve_tools if you need context-filtered results.
    return _ok_response(req_id, {"tools": router.tools_list(max_mcp_tools=512)})


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
            return _ok_response(
                req_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(auth_err, indent=2),
                        }
                    ],
                    "isError": True,
                },
            )

        # Auth passed — enterprise execution (stub: real backend call goes here)
        result_text = (
            f"[Enterprise tool: {tool_name}]\n"
            f"Arguments: {json.dumps(arguments, indent=2)}\n\n"
            "This tool requires a running enterprise backend.\n"
            "See: https://agent-corex.ai/docs/enterprise"
        )
        _log_query_event(tool_name, arguments)
        _report_usage(tool_name, "success", 0)
        return _ok_response(req_id, {"content": [{"type": "text", "text": result_text}]})

    # ── Free tool execution ────────────────────────────────────────────────
    start_ms = int(time.time() * 1000)
    try:
        result = router.execute_free_tool(tool_name, arguments)
        latency_ms = int(time.time() * 1000) - start_ms
        text = result if isinstance(result, str) else json.dumps(result, indent=2)
        _log_query_event(tool_name, arguments)
        _report_usage(tool_name, "success", latency_ms)
        return _ok_response(req_id, {"content": [{"type": "text", "text": text}]})
    except Exception as exc:
        latency_ms = int(time.time() * 1000) - start_ms
        _log_query_event(tool_name, arguments)
        _report_usage(tool_name, "failure", latency_ms)
        return _ok_response(
            req_id,
            {
                "content": [{"type": "text", "text": f"Tool execution error: {exc}"}],
                "isError": True,
            },
        )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

_RECURSION_GUARD_ENV = "AGENT_COREX_GATEWAY_DEPTH"


def run() -> None:
    """
    Start the MCP gateway server.
    Reads JSON-RPC requests from stdin, writes responses to stdout.
    Runs until stdin is closed.

    On startup:
    1. Load ~/.agent-corex/mcp.json if available
    2. Load environment variables from ~/.agent-corex/.env
    3. Inject env vars into MCP server definitions
    4. Register all tool metadata via lazy discovery (servers stopped after tool list)
    """
    import os

    log = logging.getLogger(__name__)

    # ── Recursion guard ────────────────────────────────────────────────────
    # If this process was spawned BY another agent-corex gateway (e.g. because
    # agent-corex was listed inside mcp.json), skip mcp.json loading entirely.
    # This prevents the exponential process explosion:
    #   gateway → discovers "agent-corex" in mcp.json → spawns gateway
    #           → spawns gateway → spawns gateway → 1000+ processes
    gateway_depth = int(os.environ.get(_RECURSION_GUARD_ENV, "0"))
    if gateway_depth > 0:
        log.warning(
            f"[MCP] nested gateway detected (depth={gateway_depth}) — "
            "skipping mcp.json loading to prevent recursion"
        )
        router = ToolRouter()
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
        return

    # Stamp our depth so any child processes that run agent-corex will not
    # load mcp.json (env is inherited by all subprocess.Popen children)
    os.environ[_RECURSION_GUARD_ENV] = str(gateway_depth + 1)

    # Load environment variables
    env_vars = {}
    env_file = pathlib.Path.home() / ".agent-corex" / ".env"
    if env_file.exists():
        try:
            from agent_core.env_manager import EnvManager

            env_vars = EnvManager.load_env()
            log.info(f"Loaded {len(env_vars)} environment variables")
        except Exception as e:
            log.warning(f"Could not load env file: {e}")

    # Build router immediately with built-in tools — no blocking I/O yet
    router = ToolRouter()
    mcp_manager = None

    # Load MCP tools from ~/.agent-corex/mcp.json using cache for instant startup.
    # Background thread runs live discovery and updates router as tools are found.
    local_mcp_config = pathlib.Path.home() / ".agent-corex" / "mcp.json"
    if local_mcp_config.exists():
        try:
            from agent_core.tools.mcp.mcp_loader import MCPLoader

            loader = MCPLoader(str(local_mcp_config))

            def _on_tools_discovered(server_name: str, tools: list) -> None:
                """Called by background discovery thread for each server."""
                # Stamp server name onto each tool dict so router knows its origin
                for t in tools:
                    t["server"] = server_name
                router.add_mcp_tools(tools)

            mcp_manager = loader.load_with_cache(add_tools_callback=_on_tools_discovered)
            router._mcp_manager = mcp_manager

            # Push cached tools into the router's registry immediately
            cached_tools = mcp_manager.get_all_tools()
            if cached_tools:
                router.add_mcp_tools(cached_tools)

            log.info(
                f"[MCP] gateway ready — {len(cached_tools)} tools from cache, "
                "background discovery running"
            )
        except Exception as e:
            log.warning(f"Could not load local MCP tools: {e}")

    try:
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
    finally:
        # Clean shutdown: terminate all running MCP server processes
        if mcp_manager is not None:
            log.info("[MCP] gateway shutting down — stopping all servers")
            mcp_manager.shutdown()


if __name__ == "__main__":
    import sys as _sys
    import pathlib as _pathlib

    # When run as a script (python gateway_server.py), ensure the repo root is on sys.path
    # so that `import agent_core.*` resolves to the source tree, not site-packages.
    _repo_root = str(_pathlib.Path(__file__).resolve().parents[2])
    if _repo_root not in _sys.path:
        _sys.path.insert(0, _repo_root)
    run()
