"""
Tool ranking engine for retrieval.

Supports multiple ranking strategies:
1. Keyword-only (fast, for simple queries)
2. Hybrid (keyword + embeddings, recommended)
3. Embedding-only (semantic search only)
"""

from typing import List, Dict, Any, Optional
from .scorer import score as keyword_score
from .hybrid_scorer import HybridScorer


def rank_tools(
    query: str,
    tools: List[Dict[str, Any]],
    top_k: int = 5,
    method: str = "hybrid"
) -> List[Dict[str, Any]]:
    """
    Rank tools by relevance to a query.

    Args:
        query: The search query.
        tools: List of tools to rank.
        top_k: Number of top results to return.
        method: Ranking method ('keyword', 'hybrid', or 'embedding').
               - 'keyword': Fast, exact match only
               - 'hybrid': Recommended, combines keyword + semantic
               - 'embedding': Semantic similarity only

    Returns:
        Top-k tools ranked by relevance.
    """
    if method == "keyword":
        return _rank_by_keyword(query, tools, top_k)
    elif method == "hybrid":
        return _rank_by_hybrid(query, tools, top_k)
    elif method == "embedding":
        return _rank_by_embedding(query, tools, top_k)
    else:
        raise ValueError(f"Unknown ranking method: {method}")


def _rank_by_keyword(
    query: str, tools: List[Dict[str, Any]], top_k: int
) -> List[Dict[str, Any]]:
    """Rank by keyword overlap only (fast)."""
    scored = []

    for tool in tools:
        s = keyword_score(query, tool)
        scored.append((tool, s))

    # Sort descending
    scored.sort(key=lambda x: x[1], reverse=True)

    # Filter zero scores
    ranked = [tool for tool, s in scored if s > 0]

    return ranked[:top_k]


def _rank_by_hybrid(
    query: str, tools: List[Dict[str, Any]], top_k: int
) -> List[Dict[str, Any]]:
    """Rank by hybrid scoring (keyword + embeddings)."""
    try:
        scorer = HybridScorer()
        scored = scorer.score_batch(query, tools)

        # Sort descending
        scored.sort(key=lambda x: x[1], reverse=True)

        # Return top-k (don't filter zero scores for embeddings)
        return [tool for tool, s in scored[:top_k]]
    except Exception as e:
        # Fallback to keyword-only if embedding model fails
        print(f"Warning: Embedding model failed ({e}), falling back to keyword ranking")
        return _rank_by_keyword(query, tools, top_k)


def _rank_by_embedding(
    query: str, tools: List[Dict[str, Any]], top_k: int
) -> List[Dict[str, Any]]:
    """Rank by semantic similarity only (requires embeddings)."""
    from .embeddings import EmbeddingIndexer

    try:
        indexer = EmbeddingIndexer(tools)
        return indexer.search(query, top_k)
    except Exception as e:
        # Fallback to keyword-only if embedding model fails
        print(f"Warning: Embedding model failed ({e}), falling back to keyword ranking")
        return _rank_by_keyword(query, tools, top_k)