from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent_core.tools.registry import ToolRegistry
from agent_core.retrieval.ranker import rank_tools

app = FastAPI(title="Agent-Corex", version="1.0.3")

# Enable CORS for local development and GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

tool_registry = ToolRegistry()

# Example tools (replace with MCP-loaded later)
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


@app.get("/health")
def health():
    """
    Health check endpoint for connection testing.

    Returns:
        Health status with server info and available tools
    """
    return {
        "status": "ok",
        "version": "1.0.3",
        "tools_loaded": len(tool_registry.get_all_tools()),
        "message": "Agent-Corex API is running"
    }


@app.get("/tools")
def list_tools():
    """
    List all available tools.

    Returns:
        List of all registered tools with their metadata
    """
    return {
        "tools": tool_registry.get_all_tools(),
        "total": len(tool_registry.get_all_tools())
    }


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
                "description": "Test backend connection and get version info"
            },
            {
                "name": "List Tools",
                "method": "GET",
                "path": "/tools",
                "description": "Get all available tools"
            },
            {
                "name": "List Endpoints",
                "method": "GET",
                "path": "/endpoints",
                "description": "Get documentation for all API endpoints"
            },
            {
                "name": "Retrieve Tools",
                "method": "GET",
                "path": "/retrieve_tools",
                "description": "Search and rank tools by relevance",
                "parameters": {
                    "query": "Search query describing what you need (required)",
                    "top_k": "Number of results to return (default: 5)",
                    "method": "Ranking method: 'keyword', 'hybrid', or 'embedding' (default: 'hybrid')"
                }
            }
        ]
    }


@app.get("/retrieve_tools")
def retrieve_tools(query: str, top_k: int = 5, method: str = "hybrid"):
    """
    Retrieve the most relevant tools for a given query.

    Args:
        query: Search query describing what you need
        top_k: Number of results to return (default: 5)
        method: Ranking method - 'keyword', 'hybrid', or 'embedding' (default: 'hybrid')

    Returns:
        List of tools ranked by relevance
    """
    tools = tool_registry.get_all_tools()
    ranked = rank_tools(query, tools, top_k, method=method)
    return ranked