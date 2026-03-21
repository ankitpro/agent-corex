# Agent-CoreX

🚀 **Production-ready MCP tool retrieval engine for LLMs**

Agent-CoreX solves a critical problem in LLM systems:

> When you have hundreds of tools, how do you select the *right few* without blowing up the context window?

---

## 🎉 Featured on Product Hunt!

We're live on Product Hunt! Support us by upvoting and sharing your feedback.

<a href="https://www.producthunt.com/products/agent-corex-intelligent-tool-selection" target="_blank" rel="noopener noreferrer">
  <img src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1103833&theme=light" alt="Agent-Corex on Product Hunt" width="250" height="54" />
</a>

**Quick Links:**
- 🔗 [Agent-Corex on Product Hunt](https://www.producthunt.com/products/agent-corex-intelligent-tool-selection)
- 📦 [Install from PyPI](https://pypi.org/project/agent-corex/)
- 📚 [Documentation](https://ankitpro.github.io/agent-corex/)

---

## ✨ What's New (Phase 3)

🧠 **Embedding-based semantic search** is now available! The retrieval engine now supports:

- ⚡ **Keyword matching** (fast, exact)
- 🧠 **Semantic search** (accurate, catches related terms)
- 🔀 **Hybrid ranking** (recommended, best of both)

Example:
```python
# Now catches semantically related tools, not just keyword matches
rank_tools("modify file", tools, method="hybrid")
# Returns: ["edit_file", "write_file", ...]
```

---

## 🧠 Problem

- Large toolsets → context bloat
- Too many tools → LLM confusion
- Keyword-only matching → misses related tools
- **Solution: Semantic ranking!**

---

## ⚡ Solution

Agent-Core retrieves the **top-N most relevant tools** for any query using:

1. **Keyword matching** (30% weight) - exact term overlap
2. **Semantic similarity** (70% weight) - catches related tools
3. **Fallback to keyword** if embeddings unavailable

```python
from packages.retrieval.ranker import rank_tools

# Automatically uses hybrid ranking
tools = rank_tools("edit a file", all_tools, top_k=5)
```

---

## 🔥 Key Features

- ✅ **Hybrid ranking** - 30% keyword + 70% semantic (default, recommended)
- ✅ **Three ranking methods** - keyword (fast), hybrid (balanced), embedding (accurate)
- ✅ **FAISS indexing** - fast semantic search on 1000+ tools
- ✅ **MCP integration** - load tools from Model Context Protocol servers
- ✅ **Smart fallback** - gracefully degrades if embedding model unavailable
- ✅ **FastAPI REST API** - easy integration with any application
- ✅ **CLI tool** - `agent-corex` command for quick access
- ✅ **Production-ready** - 45 comprehensive tests, all passing
- ✅ **Zero dependencies** for basic usage - only load ML models when needed
- ✅ **MIT licensed** - free for commercial use

---

## 📦 Installation

### pip (PyPI) - Recommended

```bash
pip install agent-corex
```

**That's it!** The package is ready to use immediately.

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv agent-corex-env

# Activate it
# On macOS/Linux:
source agent-corex-env/bin/activate
# On Windows:
agent-corex-env\Scripts\activate

# Install
pip install agent-corex
```

### From Source

```bash
git clone https://github.com/ankitpro/agent-corex
cd agent-corex
pip install -e .
```

**Requirements:**
- Python 3.8 or higher
- ~300MB disk space (for embedding model cache on first run)

### Verify Installation

```bash
# Check version
agent-corex version

# Try a quick command
agent-corex retrieve "edit file" --top-k 3
```

**See [GET_STARTED.md](GET_STARTED.md) for a 5-minute quick start.**

---

## 🚀 Quick Start

### 1. Use in Python

```python
from agent_core import rank_tools
from packages.tools.registry import ToolRegistry

# Create registry and add tools
registry = ToolRegistry()
registry.register({
    "name": "edit_file",
    "description": "Edit a file with line-based changes"
})
registry.register({
    "name": "write_file",
    "description": "Create or overwrite a file"
})

# Retrieve relevant tools
query = "modify a file"
results = rank_tools(query, registry.get_all_tools(), top_k=5)

for tool in results:
    print(f"✓ {tool['name']}: {tool['description']}")
```

### 2. Run the API Server

```bash
# Install uvicorn first
pip install uvicorn

# Start the server
uvicorn apps.api.main:app --reload
```

API will be available at `http://localhost:8000`

### 3. Query the API

```bash
# Default hybrid ranking (recommended)
curl "http://localhost:8000/retrieve_tools?query=edit file&top_k=5"

# Fast keyword-only
curl "http://localhost:8000/retrieve_tools?query=edit file&method=keyword"

# Pure semantic
curl "http://localhost:8000/retrieve_tools?query=edit file&method=embedding"
```

Response:

```json
[
  {
    "name": "edit_file",
    "description": "Edit a file with line-based changes"
  },
  {
    "name": "write_file",
    "description": "Create or overwrite a file"
  }
]
```

### 4. Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## 🧪 Advanced Usage

### With Custom Ranking Methods

```python
from agent_core import rank_tools

query = "edit a file"

# Method 1: Hybrid (recommended for most use cases)
results = rank_tools(query, tools, method="hybrid", top_k=5)

# Method 2: Keyword-only (fastest, for real-time apps)
results = rank_tools(query, tools, method="keyword", top_k=5)

# Method 3: Embedding-only (most semantic accuracy)
results = rank_tools(query, tools, method="embedding", top_k=5)
```

### With MCP Servers

```python
from packages.tools.mcp.mcp_loader import MCPLoader
from agent_core import rank_tools

# Load MCP servers from config
loader = MCPLoader("config/mcp.json")
manager = loader.load()

# Get all tools from MCP servers
tools = manager.get_all_tools()

# Retrieve relevant tools
results = rank_tools("edit a file", tools, top_k=5, method="hybrid")

for tool in results:
    print(f"✓ {tool['name']}: {tool['description']}")
```

### Combining Local and MCP Tools

```python
from packages.tools.registry import ToolRegistry
from packages.tools.mcp.mcp_loader import MCPLoader
from agent_core import rank_tools

# Local tools
registry = ToolRegistry()
registry.register({"name": "my_local_tool", "description": "A custom tool"})

# MCP tools
loader = MCPLoader("config/mcp.json")
manager = loader.load()

# Combine them
all_tools = registry.get_all_tools() + manager.get_all_tools()

# Retrieve from combined set
results = rank_tools("query", all_tools, top_k=5)
```

---

## 🏗️ Architecture

```
agent-corex/
├── apps/
│   └── api/
│       └── main.py              # FastAPI server
├── packages/
│   ├── retrieval/
│   │   ├── scorer.py            # Keyword-based scoring
│   │   ├── embeddings.py        # Semantic search (FAISS)
│   │   ├── hybrid_scorer.py     # Combined scoring
│   │   ├── ranker.py            # Ranking interface
│   │   └── README.md            # Detailed docs
│   ├── tools/
│   │   ├── registry.py          # Tool registry
│   │   ├── mcp/                 # MCP integration
│   │   │   ├── mcp_client.py
│   │   │   ├── mcp_loader.py
│   │   │   └── mcp_manager.py
│   │   └── README.md            # Tool docs
│   └── ...
├── config/
│   └── mcp.json                 # MCP server config
├── examples/
│   └── basic_usage.py           # Usage examples
├── tests/
│   └── test_retrieval.py        # Comprehensive tests
└── requirements.txt
```

---

## 📊 Ranking Methods Comparison

| Method | Speed | Accuracy | Model Req | Best For |
|--------|-------|----------|-----------|----------|
| **keyword** | ⚡⚡⚡ | ⭐⭐ | ❌ | Simple queries, real-time |
| **hybrid** | ⚡⚡ | ⭐⭐⭐ | ✅ | **Most use cases (default)** |
| **embedding** | ⚡ | ⭐⭐⭐⭐ | ✅ | Semantic, related terms |

---

## 🧪 Run Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test class
pytest tests/test_retrieval.py::TestRanker -v

# Run with coverage
pytest tests/ --cov=packages
```

**Test coverage includes:**
- ✅ Keyword-based scoring
- ✅ Hybrid scoring with custom weights
- ✅ Embedding-based indexing and search
- ✅ Tool registry operations
- ✅ Edge cases (empty queries, missing descriptions)
- ✅ Fallback behavior

---

## 🚀 Run Example

```bash
python examples/basic_usage.py
```

Output:
```
==================================================
Query: 'edit a file'
==================================================
1. edit_file - Edit a file with line-based changes
2. write_file - Create or overwrite a file

==================================================
Query: 'run tests'
==================================================
1. run_tests - Run test suite for the project
```

---

## 🔧 Configuration

### MCP Servers

Edit `config/mcp.json` to configure MCP servers:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "./workspace"
      ]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

### Embedding Model

The retrieval engine uses `sentence-transformers/all-MiniLM-L6-v2`:
- Small (~80MB)
- Fast
- Good quality
- Cached locally in `.agent_corex_models/`

To use a different model, modify `embeddings.py`:

```python
self.model = SentenceTransformer(
    "sentence-transformers/all-mpnet-base-v2",  # Change here
    cache_folder=".agent_corex_models"
)
```

---

## 📈 Performance

### Latency (on 1000 tools)

| Method | Latency |
|--------|---------|
| keyword | < 1ms |
| hybrid | 50-100ms |
| embedding | 50-100ms |

### Memory Usage

| Component | Memory |
|-----------|--------|
| Model | ~100MB |
| Index (1000 tools) | ~50MB |
| Total | ~150MB |

### Throughput

- **50+ requests/second** with single instance
- **Scale horizontally** by adding more API instances

---

## 📚 Complete Documentation

### Getting Started
- **[GET_STARTED.md](GET_STARTED.md)** - 5-minute quick start (recommended first step)
- **[LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)** - Comprehensive tutorial with examples
- **[OSS_READY.md](OSS_READY.md)** - Project status and features

### Package Documentation
- **[Retrieval Engine](packages/retrieval/README.md)** - Scoring, ranking, embeddings
- **[Tools Package](packages/tools/README.md)** - Tool registry and management
- **[MCP Integration](packages/tools/mcp/README.md)** - Model Context Protocol servers
- **[API Server](apps/api/README.md)** - REST endpoints and examples

### Examples & Tests
- **[Examples](examples/)** - Working code examples
- **[Tests](tests/README.md)** - How to run and write tests
- **[Configuration](config/)** - MCP server setup

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo: https://github.com/ankitpro/agent-corex
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass: `pytest tests/ -v`
5. Submit a PR with description of changes

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📊 Project Links

- **GitHub**: https://github.com/ankitpro/agent-corex
- **PyPI**: https://pypi.org/project/agent-corex/
- **Issues**: https://github.com/ankitpro/agent-corex/issues
- **Discussions**: https://github.com/ankitpro/agent-corex/discussions

---

## 🛣️ Roadmap

**Phase 1 (OSS): ✅ Complete**
- [x] Keyword-based ranking
- [x] Embedding-based ranking
- [x] Hybrid scoring
- [x] MCP integration
- [x] FastAPI server
- [x] Comprehensive tests

**Phase 2 (Hosted): Coming Soon**
- [ ] API key authentication
- [ ] Rate limiting
- [ ] Usage analytics
- [ ] Managed tool libraries
- [ ] Pre-computed embeddings

**Phase 3 (Premium): Planned**
- [ ] Fine-tuned embeddings
- [ ] Tool recommendation engine
- [ ] Success rate tracking
- [ ] Custom scoring weights per organization

---

## 📄 License

MIT - See LICENSE file

---

## 🎯 Why Agent-Core?

| Problem | Solution |
|---------|----------|
| Context bloat | Retrieve only relevant tools |
| LLM confusion | Hybrid semantic + keyword ranking |
| Keyword misses | Embedding-based semantic search |
| Cold start | Fast keyword fallback |
| Scalability | FAISS indexing for 10K+ tools |

---

## 💡 Use Cases

✅ **AI Agents** - Let agents pick the right tools from large sets
✅ **LLM APIs** - Inject only relevant tools into context
✅ **Code Search** - Find similar functions/snippets
✅ **Tool Discovery** - Help users find relevant commands
✅ **Plugin Systems** - Match user queries to plugins

---

## 📞 Support

- 📖 Read the [full documentation](packages/retrieval/README.md)
- 🐛 Open an issue on GitHub
- 💬 Join our community discussions

---

## 🚀 Get Started in 5 Minutes

1. **Install**
   ```bash
   pip install agent-corex
   ```

2. **Try it**
   ```bash
   agent-corex retrieve "edit file" --top-k 3
   ```

3. **Read the docs**
   - [GET_STARTED.md](GET_STARTED.md) - 5-minute quick start
   - [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md) - Complete tutorial

4. **Run the API**
   ```bash
   pip install uvicorn
   uvicorn apps.api.main:app --reload
   curl "http://localhost:8000/retrieve_tools?query=edit file"
   ```

That's it! You're ready to use Agent-CoreX! 🎉