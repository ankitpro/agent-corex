from __future__ import annotations

import json
import pathlib
import threading
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_core.retrieval.ranker import rank_tools

app = FastAPI(title="Agent-Corex", version="1.0.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Internal MCP tool pool (populated at startup) ────────────────────────────
# Mirrors the gateway's _mcp_registry but in FastAPI-server form.
# Populated by _load_mcp_tools() called from the startup event.
_mcp_tool_pool: list[dict] = []  # [{name, description, server, inputSchema}]
_mcp_manager = None  # MCPManager instance
_mcp_pool_lock = threading.Lock()


def _load_mcp_tools() -> None:
    """
    Load real MCP tools from ~/.agent-corex/mcp.json using the same
    MCPLoader + cache pattern as the gateway server.
    Runs in a background thread — never blocks FastAPI startup.
    """
    global _mcp_manager

    local_mcp_config = pathlib.Path.home() / ".agent-corex" / "mcp.json"
    if not local_mcp_config.exists():
        return

    try:
        from agent_core.tools.mcp.mcp_loader import MCPLoader

        loader = MCPLoader(str(local_mcp_config))

        def _on_tools_discovered(server_name: str, tools: list) -> None:
            with _mcp_pool_lock:
                for t in tools:
                    entry = {
                        "name": t.get("name", ""),
                        "description": t.get("description", ""),
                        "server": server_name,
                        "inputSchema": t.get("input_schema") or t.get("inputSchema") or {},
                    }
                    # Avoid duplicates
                    existing_names = {e["name"] for e in _mcp_tool_pool}
                    if entry["name"] and entry["name"] not in existing_names:
                        _mcp_tool_pool.append(entry)

        mgr = loader.load_with_cache(add_tools_callback=_on_tools_discovered)
        _mcp_manager = mgr

        # Push cached tools into pool immediately
        cached = mgr.get_all_tools()
        if cached:
            with _mcp_pool_lock:
                existing_names = {e["name"] for e in _mcp_tool_pool}
                for t in cached:
                    if t.get("name") and t["name"] not in existing_names:
                        _mcp_tool_pool.append(
                            {
                                "name": t["name"],
                                "description": t.get("description", ""),
                                "server": t.get("server", ""),
                                "inputSchema": t.get("schema") or {},
                            }
                        )

    except Exception as exc:
        import logging

        logging.getLogger(__name__).warning(f"[API] MCP load failed: {exc}")


# Kick off MCP loading in a background thread at module import time
threading.Thread(target=_load_mcp_tools, daemon=True, name="api-mcp-loader").start()


# ── Pydantic models ────────────────────────────────────────────────────────


class ExecuteToolRequest(BaseModel):
    """Request body for POST /execute_tool."""

    tool_name: str
    arguments: dict[str, Any] = {}


# ── Endpoints ──────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    """
    Health check endpoint for connection testing.

    Returns:
        Health status with server info and available tools
    """
    with _mcp_pool_lock:
        tool_count = len(_mcp_tool_pool)
    return {
        "status": "ok",
        "version": "1.0.3",
        "tools_loaded": tool_count,
        "message": "Agent-Corex API is running",
    }


@app.get("/tools")
def list_tools():
    """
    List all available tools from the real MCP pool.

    Returns:
        List of all registered tools with minimal metadata
    """
    with _mcp_pool_lock:
        tools = [
            {
                "name": t["name"],
                "description": t["description"],
                "server": t.get("server", ""),
                "required_inputs": (t.get("inputSchema") or {}).get("required") or [],
            }
            for t in _mcp_tool_pool
        ]
    return {"tools": tools, "total": len(tools)}


@app.get("/endpoints")
def list_endpoints():
    """
    List all available API endpoints with descriptions.

    Returns:
        List of endpoints and their purposes
    """
    return {
        "endpoints": [
            {
                "name": "Health Check",
                "method": "GET",
                "path": "/health",
                "description": "Test backend connection and get version info",
            },
            {
                "name": "List Tools",
                "method": "GET",
                "path": "/tools",
                "description": "Get all available tools",
            },
            {
                "name": "List Endpoints",
                "method": "GET",
                "path": "/endpoints",
                "description": "Get documentation for all API endpoints",
            },
            {
                "name": "Retrieve Tools",
                "method": "GET",
                "path": "/retrieve_tools",
                "description": "Search and rank tools by relevance",
                "parameters": {
                    "query": "Search query describing what you need (required)",
                    "top_k": "Number of results to return (default: 5)",
                    "method": "Ranking method: 'keyword', 'hybrid', or 'embedding' (default: 'keyword')",
                },
            },
            {
                "name": "Execute Tool",
                "method": "POST",
                "path": "/execute_tool",
                "description": "Execute a tool by name",
                "body": {"tool_name": "string", "arguments": "object"},
            },
            {
                "name": "Get Capabilities",
                "method": "GET",
                "path": "/capabilities",
                "description": "Get available capability domains",
            },
        ]
    }


@app.get("/retrieve_tools")
def retrieve_tools(query: str, top_k: int = 5, method: str = "keyword"):
    """
    Retrieve the most relevant tools for a given query from the real MCP tool pool.

    Falls back to keyword ranking (no local ML) to stay PyInstaller-safe.
    Heavy semantic ranking happens via the enterprise backend.

    Args:
        query: Search query describing what you need
        top_k: Number of results to return (default: 5)
        method: Ranking method - 'keyword', 'hybrid', or 'embedding' (default: 'keyword')

    Returns:
        List of tools ranked by relevance
    """
    with _mcp_pool_lock:
        tools = list(_mcp_tool_pool)

    if not tools:
        return []

    # Use keyword method by default — avoids loading ML models in the local server.
    safe_method = method if method == "keyword" else "keyword"
    ranked = rank_tools(query, tools, top_k, method=safe_method)
    return ranked


@app.post("/execute_tool")
def execute_tool(request: ExecuteToolRequest):
    """
    Execute a tool by name using the MCPManager.
    Accepts: {"tool_name": str, "arguments": dict}

    Returns:
        Tool execution result
    """
    if _mcp_manager is None:
        raise HTTPException(status_code=503, detail="MCP manager not yet initialized")

    # Find which server owns this tool
    with _mcp_pool_lock:
        server_name = next(
            (t["server"] for t in _mcp_tool_pool if t["name"] == request.tool_name),
            None,
        )

    if server_name is None:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown tool: {request.tool_name!r}. Call GET /retrieve_tools to find tools.",
        )

    if not _mcp_manager.ensure_server_running(server_name):
        raise HTTPException(
            status_code=503, detail=f"MCP server {server_name!r} could not be started"
        )

    client = _mcp_manager.get_client(server_name)
    if client is None:
        raise HTTPException(status_code=503, detail=f"No active client for {server_name!r}")

    try:
        result = client.call_tool(request.tool_name, request.arguments)
        return {"result": result, "tool_name": request.tool_name}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/capabilities")
def get_capabilities():
    """
    Return available capability domains derived from the loaded MCP server names.

    Returns:
        Object with available_capabilities list
    """
    from agent_core.gateway.capability_provider import get_capabilities as _get_caps

    with _mcp_pool_lock:
        server_names = list({t["server"] for t in _mcp_tool_pool if t.get("server")})

    return {"available_capabilities": _get_caps(server_names)}
