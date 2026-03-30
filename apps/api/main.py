import logging
import os
import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from agent_core.tools.registry import ToolRegistry
from agent_core.tools.mcp.mcp_loader import MCPLoader
from agent_core.retrieval.ranker import rank_tools

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent-CoreX",
    description="Production-ready MCP tool retrieval engine for LLMs",
    version="2.0.0"
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


# ═══════════════════════════════════════════════════════════════════════════════
#  V2 — Qdrant-backed intelligent retrieval
# ═══════════════════════════════════════════════════════════════════════════════

def _v2_available() -> bool:
    """True when all required V2 environment variables are set."""
    return all(
        os.getenv(k)
        for k in ("OPENAI_API_KEY", "QDRANT_URL", "QDRANT_API_KEY", "SUPABASE_URL", "SUPABASE_KEY")
    )


# ── request / response models ─────────────────────────────────────────────────

class IndexToolsRequest(BaseModel):
    tools: List[dict]
    skip_existing: bool = True


class TrackInstallationRequest(BaseModel):
    user_id: str
    tool_name: str
    server: str
    pack_id: Optional[str] = None


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.get("/v2/retrieve_tools")
def v2_retrieve_tools(
    query: str = Query(..., description="Natural language query"),
    user_id: str = Query(..., description="User ID (from auth)"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """
    V2: Semantic retrieval — returns only tools installed by *user_id*.

    Uses Qdrant vector search + keyword hybrid re-ranking.
    Results are cached (Redis if available, else in-memory).
    """
    if not _v2_available():
        raise HTTPException(
            status_code=503,
            detail="V2 retrieval not available: missing env vars (OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY, SUPABASE_URL, SUPABASE_KEY)",
        )
    if not query.strip():
        raise HTTPException(status_code=400, detail="query cannot be empty")
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id cannot be empty")

    try:
        from packages.vector.retriever import retrieve_tools as _retrieve
        return _retrieve(query=query, user_id=user_id, top_k=top_k)
    except Exception as e:
        logger.error(f"V2 retrieve_tools error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v2/index_tools")
def v2_index_tools(body: IndexToolsRequest):
    """
    V2: Enrich and index tools into Qdrant.

    Each tool in *tools* must have at minimum: name, description, server.
    Tools already indexed are skipped when skip_existing=True.
    """
    if not _v2_available():
        raise HTTPException(
            status_code=503,
            detail="V2 indexing not available: missing env vars",
        )
    if not body.tools:
        raise HTTPException(status_code=400, detail="tools list cannot be empty")

    try:
        from packages.vector.indexer import index_tools as _index
        count = _index(tools=body.tools, skip_existing=body.skip_existing)
        return {"status": "ok", "indexed": count}
    except Exception as e:
        logger.error(f"V2 index_tools error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v2/track_installation")
def v2_track_installation(body: TrackInstallationRequest):
    """
    V2: Record that a user installed a tool.

    Inserts (or upserts) into Supabase *user_tools* table.
    Also invalidates cached retrieval results for the user.
    """
    if not _v2_available():
        raise HTTPException(
            status_code=503,
            detail="V2 not available: missing env vars",
        )

    try:
        from packages.vector.retriever import track_installation as _track
        _track(
            user_id=body.user_id,
            tool_name=body.tool_name,
            server=body.server,
            pack_id=body.pack_id,
        )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"V2 track_installation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v2/index_loaded_tools")
def v2_index_loaded_tools(skip_existing: bool = True):
    """
    V2 convenience: index all tools currently loaded in memory (all_tools).

    Useful for bootstrapping after the server starts.
    """
    if not _v2_available():
        raise HTTPException(status_code=503, detail="V2 not available: missing env vars")
    if not all_tools:
        return {"status": "ok", "indexed": 0, "message": "No tools loaded in memory"}

    try:
        from packages.vector.indexer import index_tools as _index
        count = _index(tools=all_tools, skip_existing=skip_existing)
        return {"status": "ok", "indexed": count, "total_tools": len(all_tools)}
    except Exception as e:
        logger.error(f"V2 index_loaded_tools error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))