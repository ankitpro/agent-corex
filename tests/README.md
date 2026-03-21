# Tests

Comprehensive test suite for Agent-Core.

## Running Tests

### All Tests

```bash
pytest tests/ -v
```

### Specific Test File

```bash
pytest tests/test_retrieval.py -v
```

### Specific Test Class

```bash
pytest tests/test_retrieval.py::TestRanker -v
```

### Specific Test Method

```bash
pytest tests/test_retrieval.py::TestRanker::test_basic_retrieval -v
```

### With Coverage

```bash
pytest tests/ --cov=packages --cov-report=html
```

## Test Structure

### test_retrieval.py

Tests for the retrieval engine including:

**TestRanker** - Ranking functionality
- `test_basic_retrieval` - Top-ranked tool matches query
- `test_irrelevant_query` - Irrelevant queries handled correctly
- `test_top_k_limit` - top_k parameter limits results
- `test_empty_tools_list` - Empty tool list returns empty
- `test_multiple_matches` - Multiple matching tools ordered correctly

**TestScorer** - Keyword-based scoring
- `test_perfect_match` - High score for matching terms
- `test_no_overlap` - Zero score for no overlap
- `test_empty_query` - Zero score for empty query
- `test_empty_tool_description` - Handle missing description
- `test_case_insensitivity` - Case-insensitive matching

**TestHybridScorer** - Hybrid scoring (keyword + embeddings)
- `test_hybrid_score_valid_range` - Scores in [0, 1]
- `test_hybrid_batch_scoring` - Batch scoring works
- `test_semantic_similarity` - Semantic similarity working
- `test_custom_weights` - Custom weight configuration

**TestEmbeddingIndexer** - Embedding-based search
- `test_indexer_initialization` - Indexer initializes correctly
- `test_empty_indexer` - Empty indexer returns empty
- `test_semantic_search` - Semantic search finds relevant tools
- `test_add_tools_to_index` - Tools can be added to index
- `test_search_top_k_limit` - top_k parameter works

**TestRankerMethods** - Different ranking methods
- `test_keyword_ranking` - Keyword-only ranking
- `test_hybrid_ranking` - Hybrid ranking
- `test_embedding_ranking` - Embedding-only ranking
- `test_invalid_method_raises_error` - Invalid method raises error
- `test_hybrid_vs_keyword_consistency` - Methods return consistent types

**TestToolRegistry** - Tool registry operations
- `test_register_and_get` - Tools can be registered and retrieved
- `test_empty_registry` - Empty registry returns empty
- `test_multiple_registrations` - Multiple tools can be registered
- `test_register_without_description` - Tools without description work

## Test Coverage

Current coverage targets:
- **Retrieval engine**: 95%+
- **Tool registry**: 100%
- **Hybrid scoring**: 95%+
- **Embedding indexing**: 90%+

Run coverage report:
```bash
pytest tests/ --cov=packages --cov-report=term-missing
```

## Writing Tests

### Test Template

```python
def test_something_specific(self):
    """One-sentence description of what is being tested."""
    # Setup
    input_data = {"name": "tool", "description": "description"}
    
    # Execute
    result = some_function(input_data)
    
    # Assert
    assert result is not None
    assert isinstance(result, list)
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive names** - test_xxx_yyy_zzz
3. **Docstrings** - Explain what is being tested
4. **Setup/Execute/Assert** - Clear test structure
5. **Edge cases** - Empty inputs, large inputs, errors
6. **Fixtures** - Reuse common test data

### Example: Adding a Test

```python
def test_hybrid_ranking_beats_keyword_for_synonyms(self):
    """Verify hybrid ranking finds synonyms that keyword misses."""
    tools = [
        {"name": "edit", "description": "Edit files"},
        {"name": "delete", "description": "Delete files"}
    ]
    
    # "modify" is synonym for "edit"
    keyword_results = rank_tools("modify", tools, method="keyword")
    hybrid_results = rank_tools("modify", tools, method="hybrid")
    
    # Keyword should find nothing, hybrid should find edit_file
    assert len(keyword_results) == 0
    assert len(hybrid_results) > 0
    assert hybrid_results[0]["name"] == "edit"
```

## Continuous Integration

Tests run automatically on:
- Every commit
- Every pull request
- Before release

Failing tests block merging.

## Performance Tests

Monitor performance:

```python
import time

start = time.time()
result = rank_tools("query", tools)
duration = time.time() - start

print(f"Time: {duration:.3f}s")
assert duration < 0.1  # Must complete in 100ms
```

## Troubleshooting

### ImportError

```
ModuleNotFoundError: No module named 'packages'
```

Solution: Run tests from project root:
```bash
cd agent-corex
pytest tests/
```

### Model Loading Slow

First run downloads embedding model (~30-60s).
Subsequent runs cached and fast.

### Out of Memory

Tests use embedding model (~100MB).
Ensure system has 500MB+ available.

## Future Test Coverage

- [ ] Integration tests with MCP servers
- [ ] Performance benchmarks
- [ ] Load tests
- [ ] Error recovery tests
- [ ] Concurrency tests
