from fastapi import FastAPI
from packages.tools.registry import ToolRegistry
from packages.retrieval.ranker import rank_tools

app = FastAPI()

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


@app.get("/health")
def health():
    return {"status": "ok"}