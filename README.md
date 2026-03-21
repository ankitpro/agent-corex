# Agent-CoreX

🚀 **Production-ready MCP tool retrieval engine for LLMs**

Agent-CoreX solves a critical problem in LLM systems:

> When you have hundreds of tools, how do you select the *right few* without blowing up the context window?

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

- ✅ **Hybrid ranking** - keyword + semantic (default)
- ✅ **Multiple ranking methods** - keyword, hybrid, embedding-only
- ✅ **FAISS indexing** - fast semantic search
- ✅ **MCP integration** - load tools from MCP servers
- ✅ **Smart fallback** - degraded gracefully if models unavailable
- ✅ **FastAPI** - simple REST API
- ✅ **Comprehensive tests** - 25+ test cases

---

## 📦 Installation

### Quick Install (Recommended)

**macOS/Linux:**
```bash
curl -fsSL https://raw.githubusercontent.com/your-org/agent-corex/main/install-curl.sh | bash
```

**Windows:**
```cmd
pip install agent-corex
```

### pip (PyPI)

```bash
pip install agent-corex
```

With optional dependencies:
```bash
pip install agent-corex[redis]      # Redis support
pip install agent-corex[dev]        # Dev tools
pip install agent-corex[dev,redis]  # Everything
```

### From Source

```bash
git clone https://github.com/your-org/agent-corex
cd agent-corex
pip install -e .
```

**Requirements:**
- Python 3.8+
- ~300MB disk (for embedding model cache)

**See [INSTALL.md](INSTALL.md) for detailed installation options.**

---

## 🚀 Quick Start

### 1. Run the API

```bash
uvicorn apps.api.main:app --reload
```

API will be available at `http://localhost:8000`

### 2. Retrieve Tools

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

### 3. Health Check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## 🧪 Usage in Code

### Basic Python Usage

```python
from packages.retrieval.ranker import rank_tools
from packages.tools.registry import ToolRegistry

# Create registry and add tools
registry = ToolRegistry()
registry.register({"name": "edit_file", "description": "Edit files"})
registry.register({"name": "write_file", "description": "Write files"})

# Retrieve tools
query = "edit a file"
results = rank_tools(query, registry.get_all_tools(), top_k=5)

for tool in results:
    print(f"- {tool['name']}: {tool['description']}")
```

### With MCP Servers

```python
from packages.tools.mcp.mcp_loader import MCPLoader
from packages.tools.mcp.mcp_manager import MCPManager
from packages.retrieval.ranker import rank_tools

# Load MCP servers
loader = MCPLoader("config/mcp.json")
manager = loader.load()

# Get all tools from MCP servers
tools = manager.get_all_tools()

# Retrieve relevant tools
results = rank_tools("edit a file", tools, top_k=5, method="hybrid")
```

### Choosing Ranking Methods

```python
from packages.retrieval.ranker import rank_tools

query = "edit a file"

# Method 1: Hybrid (recommended for most use cases)
results = rank_tools(query, tools, method="hybrid")

# Method 2: Keyword-only (fastest, for real-time)
results = rank_tools(query, tools, method="keyword")

# Method 3: Embedding-only (most semantic)
results = rank_tools(query, tools, method="embedding")
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
- Cached locally in `.agent_core_models/`

To use a different model, modify `embeddings.py`:

```python
self.model = SentenceTransformer(
    "sentence-transformers/all-mpnet-base-v2",  # Change here
    cache_folder=".agent_core_models"
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

## 📚 Documentation

- [Retrieval Engine Docs](packages/retrieval/README.md)
- [Tools Package Docs](packages/tools/README.md)
- [API Examples](examples/basic_usage.py)

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a PR

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

## 🚀 Get Started Now

```bash
git clone https://github.com/your-org/agent-corex
cd agent-corex
pip install -r requirements.txt
uvicorn apps.api.main:app --reload
curl "http://localhost:8000/retrieve_tools?query=your query"
```