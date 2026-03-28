"""
Agent-Core: Fast, accurate MCP tool retrieval engine for LLMs with semantic search.

Provides multiple ranking methods for selecting the most relevant tools from large sets.
"""

__version__ = "1.1.2"
__author__ = "Ankit Agarwal"
__email__ = "ankitagarwalpro@gmail.com"

# Heavy ML imports are kept lazy so the CLI binary (built with PyInstaller)
# does not need to bundle torch / faiss / sentence-transformers at package-import
# time.  Import them directly when you actually need them:
#   from agent_core.retrieval.ranker import rank_tools
#   from agent_core.tools.registry import ToolRegistry
#   from agent_core.tools.mcp.mcp_loader import MCPLoader

__all__ = [
    "rank_tools",
    "ToolRegistry",
    "MCPLoader",
]


def __getattr__(name: str):
    if name == "rank_tools":
        from agent_core.retrieval.ranker import rank_tools

        return rank_tools
    if name == "ToolRegistry":
        from agent_core.tools.registry import ToolRegistry

        return ToolRegistry
    if name == "MCPLoader":
        from agent_core.tools.mcp.mcp_loader import MCPLoader

        return MCPLoader
    raise AttributeError(f"module 'agent_core' has no attribute {name!r}")
