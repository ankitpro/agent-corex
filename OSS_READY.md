# Agent-CoreX: Open Source Ready ✅

## Status: Production Ready

Agent-CoreX has been thoroughly tested, documented, and verified for open source release.

### Quick Stats

| Metric | Value |
|--------|-------|
| **Tests Passing** | 45/45 ✅ |
| **Code Coverage** | All modules covered |
| **Documentation** | 8 README files + guides |
| **Examples** | 2 working scripts |
| **PyPI Status** | Live & installable |
| **GitHub Actions** | Automated testing & publishing |
| **Code Quality** | No orphaned/broken files |

---

## What's Included

### Phase 1: Tool Retrieval
- ✅ Tool Registry for registering tools
- ✅ Keyword-based ranking (exact matches)
- ✅ Fast retrieval for real-time applications

### Phase 2: MCP Integration  
- ✅ MCP Client for managing MCP servers
- ✅ MCP Loader for loading configurations
- ✅ MCP Manager for aggregating tools from multiple servers
- ✅ Support for stdio and stdio transport

### Phase 3: Semantic Search
- ✅ Embedding-based indexing using sentence-transformers
- ✅ FAISS for efficient similarity search
- ✅ Hybrid ranking (keyword + semantic)
- ✅ Graceful fallback when embeddings unavailable
- ✅ Semantic matching catches related tools

---

## Getting Started

### Installation
```bash
pip install agent-corex
```

### Quick Example
```python
from agent_core import rank_tools
from packages.tools.registry import ToolRegistry

registry = ToolRegistry()
registry.register({"name": "edit_file", "description": "Edit files"})
registry.register({"name": "run_tests", "description": "Run tests"})

tools = registry.get_all_tools()

# Find tools for a query
results = rank_tools("modify code", tools, top_k=2, method="hybrid")
# Returns: [edit_file, run_tests]
```

### CLI
```bash
agent-corex retrieve "edit file" --top-k 3 --method hybrid
agent-corex start --host 0.0.0.0 --port 8000
```

### API
```bash
curl "http://localhost:8000/retrieve_tools?query=edit+file&top_k=5"
```

---

## Documentation

### For Users
- **[README.md](README.md)** - Full feature guide
- **[GET_STARTED.md](GET_STARTED.md)** - 5-minute quick start
- **[LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)** - Comprehensive tutorial
- **[examples/basic_usage.py](examples/basic_usage.py)** - Working example

### For Developers
- **[packages/retrieval/README.md](packages/retrieval/README.md)** - Retrieval engine
- **[packages/tools/README.md](packages/tools/README.md)** - Tool registry
- **[packages/tools/mcp/README.md](packages/tools/mcp/README.md)** - MCP integration
- **[apps/api/README.md](apps/api/README.md)** - API server
- **[tests/README.md](tests/README.md)** - Test guide

### Configurations
- **[config/README.md](config/README.md)** - MCP configuration guide

---

## Testing

All 45 tests pass across 3 test suites:

```bash
pytest tests/ -v
# test_retrieval.py: 20 tests (ranker, scorer, registry, embeddings)
# test_mcp.py: 9 tests (MCP manager, client)
# test_api.py: 16 tests (API endpoints)
```

### Test Coverage
- ✅ Ranking methods (keyword, hybrid, embedding)
- ✅ Edge cases (empty lists, empty queries, no matches)
- ✅ Semantic matching (related terms)
- ✅ API endpoints (health, retrieve_tools)
- ✅ Tool registration and retrieval
- ✅ MCP integration

---

## Features

### Ranking Methods

1. **Keyword** (⚡⚡⚡ Fast)
   - Exact term matching
   - < 1ms per query
   - Good for real-time

2. **Hybrid** (⚡⚡ Medium) - Recommended
   - 30% keyword matching
   - 70% semantic similarity
   - Best balance of speed and accuracy

3. **Embedding** (⚡ Slower)
   - Pure semantic matching
   - 50-100ms per query
   - Most accurate for intent

### Capabilities

- **Smart Tool Selection**: Pick top-N tools for any query
- **Semantic Understanding**: Catches related tools even without keyword overlap
- **MCP Integration**: Load tools from multiple MCP servers
- **API & CLI**: Multiple interfaces for integration
- **Graceful Fallback**: Works even if embedding model unavailable

---

## Architecture

```
Query Input
    ↓
Keyword Scorer (30% weight)
    ↓
Embedding Indexer (70% weight) 
    ↓
Hybrid Scorer
    ↓
Ranker (sorts by score)
    ↓
Top-K Results
```

---

## Performance

### Benchmarks (on 8 tools)

| Method | Speed | Accuracy |
|--------|-------|----------|
| Keyword | < 1ms | ⭐⭐⭐ |
| Hybrid | 50-100ms | ⭐⭐⭐⭐ |
| Embedding | 50-100ms | ⭐⭐⭐⭐⭐ |

*Note: First embedding call loads model (~80MB), subsequent calls cached*

---

## Use Cases

1. **LLM Tool Selection**: Reduce context window by selecting relevant tools
2. **API Discovery**: Help users find the right API endpoint
3. **Documentation Search**: Find relevant docs for a query
4. **Service Discovery**: Find microservices by capability
5. **Plugin Management**: Select plugins for a task

---

## Package Information

- **Name**: agent-corex
- **Version**: 1.0.0
- **Author**: Ankit Agarwal <ankitagarwalpro@gmail.com>
- **License**: MIT
- **Repository**: https://github.com/ankitpro/agent-corex
- **PyPI**: https://pypi.org/project/agent-corex/
- **Python**: 3.8+

---

## Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **typer**: CLI framework
- **sentence-transformers**: Embeddings
- **faiss-cpu**: Vector search

---

## Next Steps

1. **Try Locally**: `pip install agent-corex && python examples/basic_usage.py`
2. **Test Integration**: Use in your LLM application
3. **Contribute**: Issues and PRs welcome on GitHub
4. **Deploy**: Use Docker, Cloud Run, or any ASGI server

---

## Support

- **Issues**: https://github.com/ankitpro/agent-corex/issues
- **Discussions**: https://github.com/ankitpro/agent-corex/discussions
- **Documentation**: See README and guides above

---

## License

MIT License - See LICENSE file for details

---

**Agent-CoreX is ready for production use!** 🚀

