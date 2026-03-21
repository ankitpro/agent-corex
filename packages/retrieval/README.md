# Retrieval Engine

The retrieval engine is the core of Agent-Core. It handles scoring and ranking tools based on query relevance using multiple strategies.

## Components

### 1. **scorer.py** - Keyword-based Scoring
Fast, exact-match keyword overlap scoring.

```python
from packages.retrieval.scorer import score

tool = {"name": "edit_file", "description": "Edit files"}
keyword_score = score("edit", tool)  # Returns 1.0
```

**Characteristics:**
- ⚡ Very fast (no ML models)
- 🎯 Exact keyword matching only
- 📊 Score = overlap / query_length

### 2. **embeddings.py** - Semantic Search
FAISS-based embedding indexing for semantic similarity.

```python
from packages.retrieval.embeddings import EmbeddingIndexer

indexer = EmbeddingIndexer(tools)
results = indexer.search("edit a file", top_k=5)
```

**Characteristics:**
- 🧠 Semantic understanding (catches related terms)
- 📦 Pre-cached models
- 🔍 FAISS indexing for efficient search
- ⏱️ Slower but more accurate

### 3. **hybrid_scorer.py** - Combined Ranking
Hybrid scoring combining keyword + embedding approaches.

```python
from packages.retrieval.hybrid_scorer import HybridScorer

scorer = HybridScorer()
score = scorer.score("edit file", tool)
```

**Default weights:**
- 30% keyword matching
- 70% embedding similarity
- Optimized for semantic search + keyword boosting

### 4. **ranker.py** - Tool Ranking
Main ranking interface supporting multiple strategies.

```python
from packages.retrieval.ranker import rank_tools

# Method 1: Keyword-only (fastest)
results = rank_tools(query, tools, method="keyword")

# Method 2: Hybrid (recommended)
results = rank_tools(query, tools, method="hybrid")

# Method 3: Embedding-only (most semantic)
results = rank_tools(query, tools, method="embedding")
```

## Ranking Methods

| Method | Speed | Accuracy | Best For |
|--------|-------|----------|----------|
| **keyword** | ⚡⚡⚡ | ⭐⭐ | Simple, exact queries |
| **hybrid** | ⚡⚡ | ⭐⭐⭐ | Most use cases (default) |
| **embedding** | ⚡ | ⭐⭐⭐⭐ | Semantic, related terms |

## Usage Examples

### Basic Usage
```python
from packages.retrieval.ranker import rank_tools

query = "edit a file"
results = rank_tools(query, tools, top_k=5)

for tool in results:
    print(f"- {tool['name']}: {tool['description']}")
```

### With Different Methods
```python
# Fast keyword-only (for real-time apps)
fast_results = rank_tools(query, tools, method="keyword", top_k=3)

# Semantic search (for better accuracy)
semantic_results = rank_tools(query, tools, method="embedding", top_k=5)

# Balanced approach (recommended)
balanced = rank_tools(query, tools, method="hybrid", top_k=5)
```

### Custom Hybrid Weights
```python
from packages.retrieval.hybrid_scorer import HybridScorer

# 50/50 keyword and embedding
scorer = HybridScorer(keyword_weight=0.5, embedding_weight=0.5)
score = scorer.score(query, tool)
```

## Model Caching

The embedding model (`sentence-transformers/all-MiniLM-L6-v2`) is cached at the class level:
- ✅ Loaded once per process
- ✅ Shared across instances
- ✅ Stored in `.agent_core_models/`

## Performance Notes

### Keyword Scoring
- **Time:** < 1ms per query
- **Memory:** Minimal
- **Best for:** Real-time applications with simple queries

### Embedding Search
- **Time:** 10-100ms per query (first load slower)
- **Memory:** ~100MB for model + index
- **Best for:** High-quality semantic matching

### Hybrid Scoring
- **Time:** 10-100ms per query
- **Memory:** ~100MB
- **Best for:** Balanced speed and accuracy

## Fallback Behavior

If the embedding model fails to load:
1. Hybrid ranking → falls back to keyword ranking
2. Embedding ranking → falls back to keyword ranking
3. Keyword ranking → always works (no dependencies)

## Testing

Run tests for the retrieval engine:

```bash
pytest tests/test_retrieval.py -v
```

Tests cover:
- ✅ Keyword-based scoring and ranking
- ✅ Hybrid scoring with custom weights
- ✅ Embedding-based indexing and search
- ✅ Edge cases (empty queries, missing descriptions)
- ✅ Fallback behavior

## Integration with API

The `/retrieve_tools` endpoint supports all ranking methods:

```bash
# Default (hybrid)
curl "http://localhost:8000/retrieve_tools?query=edit file&top_k=5"

# Keyword-only
curl "http://localhost:8000/retrieve_tools?query=edit file&method=keyword"

# Embedding-only
curl "http://localhost:8000/retrieve_tools?query=edit file&method=embedding"
```

## Future Enhancements

- [ ] Fine-tuned embeddings for specific tool domains
- [ ] Cross-lingual semantic search
- [ ] Tool usage frequency weighting
- [ ] Custom model selection
- [ ] Embedding caching and persistence
- [ ] Real-time index updates
