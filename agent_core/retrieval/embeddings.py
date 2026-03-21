"""
Embedding-based tool indexing and semantic search using FAISS and sentence-transformers.

This module provides semantic search capabilities for tools using pre-trained embeddings.
Tools are indexed by their name and description, enabling semantic similarity matching
for queries that aren't exact keyword matches.
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Dict, Any, Optional


class EmbeddingIndexer:
    """
    FAISS-based semantic search indexer for tools.

    Uses sentence-transformers to generate embeddings for tool names and descriptions,
    then uses FAISS for efficient similarity search.

    Attributes:
        model: Cached SentenceTransformer model (shared across instances)
        tools: List of tools in the index
        index: FAISS index for similarity search
    """

    _model = None  # Class-level cache to avoid reloading model

    def __init__(self, tools: Optional[List[Dict[str, Any]]] = None):
        """
        Initialize the embedding indexer.

        Args:
            tools: Optional list of tools to index. Each tool should have 'name' and 'description'.
        """
        # Load model once and cache at class level
        if EmbeddingIndexer._model is None:
            EmbeddingIndexer._model = SentenceTransformer(
                "sentence-transformers/all-MiniLM-L6-v2", cache_folder=".agent_corex_models"
            )

        self.model = EmbeddingIndexer._model
        self.tools = tools or []
        self.index = None

        if self.tools:
            self._build_index(self.tools)

    def _build_index(self, tools: List[Dict[str, Any]]) -> None:
        """
        Build FAISS index from tools.

        Args:
            tools: List of tools to index.
        """
        texts = [f"{t['name']} {t.get('description', '')}" for t in tools]

        embeddings = self.model.encode(texts)
        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(dim)
        self.index.add(np.array(embeddings, dtype=np.float32))

    def add_tools(self, tools: List[Dict[str, Any]]) -> None:
        """
        Add new tools to the index.

        Args:
            tools: List of tools to add.
        """
        texts = [f"{t['name']} {t.get('description', '')}" for t in tools]

        embeddings = self.model.encode(texts)

        if self.index is None:
            dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dim)

        self.index.add(np.array(embeddings, dtype=np.float32))

        for tool in tools:
            self.tools.append(tool)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for tools semantically similar to the query.

        Args:
            query: The search query.
            top_k: Number of top results to return.

        Returns:
            List of tools sorted by semantic similarity to the query.
        """
        if top_k is None:
            top_k = 5

        if self.index is None or not self.tools:
            return []

        query_vec = self.model.encode([query])
        D, I = self.index.search(np.array(query_vec, dtype=np.float32), min(top_k, len(self.tools)))

        results = [self.tools[i] for i in I[0] if 0 <= i < len(self.tools)]

        return results
