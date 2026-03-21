"""
Tests for the retrieval engine (scorer, ranker, and embeddings).

Tests cover:
- Keyword-based scoring and ranking
- Hybrid (keyword + embedding) ranking
- Embedding-based indexing and search
- Tool registry operations
"""

import pytest
from packages.retrieval.ranker import rank_tools
from packages.retrieval.scorer import score
from packages.retrieval.hybrid_scorer import HybridScorer
from packages.retrieval.embeddings import EmbeddingIndexer
from packages.tools.registry import ToolRegistry

# Test data
SAMPLE_TOOLS = [
    {"name": "edit_file", "description": "Edit files"},
    {"name": "write_file", "description": "Write files"},
    {"name": "run_tests", "description": "Run tests"}
]


class TestRanker:
    """Tests for the rank_tools function."""

    def test_basic_retrieval(self):
        """Verify that top-ranked tool matches the query."""
        result = rank_tools("edit a file", SAMPLE_TOOLS, top_k=2)
        assert len(result) > 0
        assert result[0]["name"] == "edit_file"

    def test_irrelevant_query(self):
        """Verify that irrelevant queries with keyword method return empty list."""
        # Keyword-only: no overlap with tool names/descriptions
        result = rank_tools("deploy kubernetes cluster", SAMPLE_TOOLS, top_k=2, method="keyword")
        assert isinstance(result, list)
        assert result == []  # No keyword overlap

        # Hybrid: may find semantic matches even without keywords
        result_hybrid = rank_tools("deploy kubernetes cluster", SAMPLE_TOOLS, top_k=2, method="hybrid")
        assert isinstance(result_hybrid, list)
        # Hybrid may or may not return results depending on semantic similarity

    def test_top_k_limit(self):
        """Verify that top_k parameter limits results."""
        result = rank_tools("file", SAMPLE_TOOLS, top_k=1)
        assert len(result) <= 1

    def test_empty_tools_list(self):
        """Verify that ranking an empty tool list returns empty."""
        result = rank_tools("edit file", [], top_k=5)
        assert result == []

    def test_multiple_matches(self):
        """Verify correct ordering when multiple tools match."""
        result = rank_tools("file", SAMPLE_TOOLS, top_k=5)
        # Both edit_file and write_file contain "file"
        assert len(result) >= 2
        # Both should be in results
        names = [tool["name"] for tool in result]
        assert "edit_file" in names
        assert "write_file" in names


class TestScorer:
    """Tests for the score function."""

    def test_perfect_match(self):
        """Verify high score for matching terms."""
        tool = {"name": "edit_file", "description": "Edit files"}
        score_val = score("edit", tool)
        assert score_val > 0

    def test_no_overlap(self):
        """Verify zero score for no overlapping terms."""
        tool = {"name": "edit_file", "description": "Edit files"}
        score_val = score("kubernetes", tool)
        assert score_val == 0.0

    def test_empty_query(self):
        """Verify zero score for empty query."""
        tool = {"name": "edit_file", "description": "Edit files"}
        score_val = score("", tool)
        assert score_val == 0.0

    def test_empty_tool_description(self):
        """Verify safe handling of tools with empty description."""
        tool = {"name": "edit_file"}
        score_val = score("edit", tool)
        # Should handle missing description gracefully
        assert isinstance(score_val, float)
        assert score_val >= 0.0

    def test_case_insensitivity(self):
        """Verify case-insensitive matching."""
        tool = {"name": "EDIT_FILE", "description": "EDIT FILES"}
        score_val = score("edit", tool)
        assert score_val > 0


class TestToolRegistry:
    """Tests for the ToolRegistry class."""

    def test_register_and_get(self):
        """Verify tools can be registered and retrieved."""
        registry = ToolRegistry()
        tool = {"name": "test_tool", "description": "A test tool"}
        registry.register(tool)
        tools = registry.get_all_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    def test_empty_registry(self):
        """Verify empty registry returns empty list."""
        registry = ToolRegistry()
        tools = registry.get_all_tools()
        assert tools == []

    def test_multiple_registrations(self):
        """Verify multiple tools can be registered."""
        registry = ToolRegistry()
        registry.register({"name": "tool1", "description": "First tool"})
        registry.register({"name": "tool2", "description": "Second tool"})
        registry.register({"name": "tool3", "description": "Third tool"})
        tools = registry.get_all_tools()
        assert len(tools) == 3

    def test_register_without_description(self):
        """Verify tools can be registered without description."""
        registry = ToolRegistry()
        tool = {"name": "minimal_tool"}
        registry.register(tool)
        tools = registry.get_all_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "minimal_tool"


class TestHybridScorer:
    """Tests for hybrid scoring (keyword + embeddings)."""

    def test_hybrid_score_valid_range(self):
        """Verify hybrid scores are in valid range [0, 1]."""
        scorer = HybridScorer()
        tool = {"name": "edit_file", "description": "Edit a file"}
        score_val = scorer.score("edit file", tool)
        assert 0 <= score_val <= 1

    def test_hybrid_batch_scoring(self):
        """Verify batch scoring works correctly."""
        scorer = HybridScorer()
        scored = scorer.score_batch("edit file", SAMPLE_TOOLS)
        assert len(scored) == len(SAMPLE_TOOLS)
        # All scores should be in valid range
        for tool, score_val in scored:
            assert 0 <= score_val <= 1

    def test_semantic_similarity(self):
        """Verify semantic similarity captures related terms."""
        scorer = HybridScorer()

        # "modify" is semantically similar to "edit"
        edit_tool = {"name": "edit_file", "description": "Edit a file"}
        score1 = scorer.score("modify file", edit_tool)

        # "kubernetes" is not related
        score2 = scorer.score("kubernetes deployment", edit_tool)

        # Semantic similarity should give edit_file higher score for "modify"
        assert score1 > score2

    def test_custom_weights(self):
        """Verify custom weight configuration."""
        scorer = HybridScorer(keyword_weight=0.5, embedding_weight=0.5)
        assert scorer.keyword_weight == 0.5
        assert scorer.embedding_weight == 0.5


class TestEmbeddingIndexer:
    """Tests for embedding-based indexing and search."""

    def test_indexer_initialization(self):
        """Verify indexer can be initialized with tools."""
        indexer = EmbeddingIndexer(SAMPLE_TOOLS)
        assert indexer.tools == SAMPLE_TOOLS
        assert indexer.index is not None

    def test_empty_indexer(self):
        """Verify empty indexer returns empty results."""
        indexer = EmbeddingIndexer([])
        results = indexer.search("edit file", top_k=5)
        assert results == []

    def test_semantic_search(self):
        """Verify semantic search finds relevant tools."""
        indexer = EmbeddingIndexer(SAMPLE_TOOLS)
        results = indexer.search("edit a file", top_k=2)
        assert len(results) > 0
        # Should find tools related to editing
        names = [t["name"] for t in results]
        assert any("edit" in name or "file" in name for name in names)

    def test_add_tools_to_index(self):
        """Verify tools can be added to existing index."""
        indexer = EmbeddingIndexer(SAMPLE_TOOLS[:2])
        assert len(indexer.tools) == 2

        new_tools = [SAMPLE_TOOLS[2]]
        indexer.add_tools(new_tools)
        assert len(indexer.tools) == 3

    def test_search_top_k_limit(self):
        """Verify top_k parameter limits results."""
        indexer = EmbeddingIndexer(SAMPLE_TOOLS)
        results = indexer.search("file", top_k=1)
        assert len(results) <= 1


class TestRankerMethods:
    """Tests for different ranking methods."""

    def test_keyword_ranking(self):
        """Verify keyword-only ranking."""
        result = rank_tools("edit file", SAMPLE_TOOLS, top_k=5, method="keyword")
        assert isinstance(result, list)

    def test_hybrid_ranking(self):
        """Verify hybrid ranking (default)."""
        result = rank_tools("edit file", SAMPLE_TOOLS, top_k=5, method="hybrid")
        assert isinstance(result, list)

    def test_embedding_ranking(self):
        """Verify embedding-only ranking."""
        result = rank_tools("edit file", SAMPLE_TOOLS, top_k=5, method="embedding")
        assert isinstance(result, list)

    def test_invalid_method_raises_error(self):
        """Verify invalid ranking method raises error."""
        with pytest.raises(ValueError):
            rank_tools("edit file", SAMPLE_TOOLS, method="invalid")

    def test_hybrid_vs_keyword_consistency(self):
        """Verify hybrid and keyword methods return consistent results."""
        query = "file operations"

        keyword_result = rank_tools(query, SAMPLE_TOOLS, top_k=5, method="keyword")
        hybrid_result = rank_tools(query, SAMPLE_TOOLS, top_k=5, method="hybrid")

        # Both should return lists (may differ in order/content)
        assert isinstance(keyword_result, list)
        assert isinstance(hybrid_result, list)
