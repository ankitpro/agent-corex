"""
Hybrid scoring system combining keyword-based and embedding-based relevance.

This module provides scoring methods that combine:
1. Keyword overlap (fast, exact matching)
2. Semantic similarity via embeddings (catches related tools)

The hybrid approach gives the best of both worlds: speed + accuracy.
"""

from typing import List, Dict, Any, Tuple, Optional
from .scorer import score as keyword_score
from .embeddings import EmbeddingIndexer
from sentence_transformers import SentenceTransformer
import numpy as np


class HybridScorer:
    """
    Combines keyword-based and embedding-based scoring.

    Uses a weighted combination of:
    - Keyword overlap score (0.3 weight)
    - Embedding similarity score (0.7 weight)

    This gives semantic search the priority while still considering exact keyword matches.
    """

    def __init__(self, keyword_weight: float = 0.3, embedding_weight: float = 0.7):
        """
        Initialize the hybrid scorer.

        Args:
            keyword_weight: Weight for keyword-based scoring (0-1).
            embedding_weight: Weight for embedding-based scoring (0-1).
        """
        self.keyword_weight = keyword_weight
        self.embedding_weight = embedding_weight

        # Normalize weights
        total = keyword_weight + embedding_weight
        self.keyword_weight /= total
        self.embedding_weight /= total

        # Initialize the embedding model
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            cache_folder=".agent_corex_models"
        )

    def score(self, query: str, tool: Dict[str, Any]) -> float:
        """
        Compute hybrid score for a tool.

        Args:
            query: The search query.
            tool: Tool dictionary with 'name' and 'description'.

        Returns:
            Hybrid score between 0 and 1.
        """
        # Get keyword score
        kw_score = keyword_score(query, tool)

        # Get embedding score
        query_vec = self.model.encode([query])
        tool_text = f"{tool['name']} {tool.get('description', '')}"
        tool_vec = self.model.encode([tool_text])

        # Cosine similarity (convert L2 distance to similarity)
        # FAISS uses L2 distance, so we convert: similarity = 1 / (1 + distance)
        similarity = np.dot(query_vec[0], tool_vec[0]) / (
            np.linalg.norm(query_vec[0]) * np.linalg.norm(tool_vec[0])
        )
        # Normalize to 0-1 range
        embedding_score = (similarity + 1) / 2

        # Combine scores
        hybrid_score = (
            self.keyword_weight * kw_score +
            self.embedding_weight * embedding_score
        )

        return hybrid_score

    def score_batch(
        self, query: str, tools: List[Dict[str, Any]]
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Score multiple tools efficiently.

        Args:
            query: The search query.
            tools: List of tools to score.

        Returns:
            List of (tool, score) tuples.
        """
        scored = []

        for tool in tools:
            s = self.score(query, tool)
            scored.append((tool, s))

        return scored
