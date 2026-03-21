"""
Agent-Core: Fast, accurate MCP tool retrieval engine for LLMs with semantic search.

Provides multiple ranking methods for selecting the most relevant tools from large sets.
"""

__version__ = "1.0.0"
__author__ = "Ankit Agarwal"
__email__ = "ankitagarwalpro@gmail.com"

from agent_core.retrieval.ranker import rank_tools
from agent_core.tools.registry import ToolRegistry
from agent_core.tools.mcp.mcp_loader import MCPLoader

__all__ = [
    "rank_tools",
    "ToolRegistry",
    "MCPLoader",
]
