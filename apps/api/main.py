import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from agent_core.tools.registry import ToolRegistry
from agent_core.tools.mcp.mcp_loader import MCPLoader
from agent_core.retrieval.ranker import rank_tools

app = FastAPI(
    title="Agent-CoreX",
    description="Production-ready MCP tool retrieval engine for LLMs",
    version="1.0.0"
)

# Initialize tool registry
tool_registry = ToolRegistry()
all_tools = []


def load_tools():
    """
    Load tools from multiple sources:
    1. Local tool registry
    2. MCP servers (from config/mcp.json or env-specified config)
    """
    global all_tools

    # Load example/local tools
    tool_registry.register({
        "name": "edit_file",
        "description": "Edit a file with line-based changes"
    })
    tool_registry.register({
        "name": "write_file",
        "description": "Create or overwrite a file"
    })
    tool_registry.register({
        "name": "run_tests",
        "description": "Run test suite"
    })

    # Get local tools
    all_tools = tool_registry.get_all_tools().copy()

    # Try to load MCP servers
    mcp_config = os.getenv("MCP_CONFIG", "config/mcp.json")

    if Path(mcp_config).exists():
        try:
            loader = MCPLoader(mcp_config)
            manager = loader.load()
            mcp_tools = manager.get_all_tools()
            all_tools.extend(mcp_tools)
            print(f"[OK] Loaded {len(mcp_tools)} tools from MCP servers")
        except Exception as e:
            print(f"[WARN] Could not load MCP servers: {e}")
            print(f"  Continuing with {len(all_tools)} local tools only")
    else:
        print(f"[INFO] No MCP config found at {mcp_config}")
        print(f"  Using {len(all_tools)} local tools only")
        print(f"  To add MCP tools, create {mcp_config} or set MCP_CONFIG env var")


# Load tools on startup
load_tools()


@app.get("/retrieve_tools")
def retrieve_tools(query: str, top_k: int = 5, method: str = "hybrid"):
    """
    Retrieve the most relevant tools for a given query.

    Query Parameters:
    - query (string, required): Search query describing what you need
    - top_k (integer, optional, default: 5): Number of results to return
    - method (string, optional, default: 'hybrid'): Ranking method
      - 'keyword': Fast keyword-only matching
      - 'hybrid': Recommended, combines keyword + semantic
      - 'embedding': Pure semantic similarity

    Returns:
        List of tools ranked by relevance

    Example:
        GET /retrieve_tools?query=edit file&top_k=5&method=hybrid
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query parameter cannot be empty")

    if method not in ["keyword", "hybrid", "embedding"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ranking method: {method}. Must be 'keyword', 'hybrid', or 'embedding'"
        )

    try:
        ranked = rank_tools(query, all_tools, top_k, method=method)
        return ranked
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ranking tools: {str(e)}")


@app.get("/health")
def health():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok",
        "tools_loaded": len(all_tools),
        "version": "1.0.0"
    }


@app.get("/tools")
def list_all_tools(limit: int = 100):
    """
    List all available tools.

    Query Parameters:
    - limit (integer, optional, default: 100): Maximum number of tools to return

    Returns:
        List of all available tools

    Example:
        GET /tools?limit=50
    """
    return all_tools[:limit]


@app.get("/tools/{tool_name}")
def get_tool(tool_name: str):
    """
    Get details for a specific tool by name.

    Path Parameters:
    - tool_name (string): Name of the tool

    Returns:
        Tool details including name and description

    Example:
        GET /tools/edit_file
    """
    for tool in all_tools:
        if tool.get("name") == tool_name:
            return tool

    raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@app.post("/reload")
def reload_tools():
    """
    Reload tools from configuration files.
    Useful after updating config/mcp.json or MCP_CONFIG.

    Returns:
        Status message with number of tools loaded
    """
    global all_tools, tool_registry

    # Reset
    tool_registry = ToolRegistry()
    all_tools = []

    # Reload
    load_tools()

    return {
        "status": "reloaded",
        "tools_loaded": len(all_tools),
        "message": f"Successfully loaded {len(all_tools)} tools"
    }