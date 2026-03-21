# Agent-Core - Quick Start Guide

Get up and running with Agent-Core in 2 minutes! 🚀

## Installation

### Option 1: From PyPI (Recommended)
```bash
pip install agent-corex
```

### Option 2: From Source
```bash
git clone https://github.com/ankitpro/agent-corex
cd agent-corex
pip install -e .
```

### Option 3: Docker (Coming Soon)
```bash
docker run -p 8000:8000 agent-corex:latest
```

---

## Usage

### 1. Command Line (Fastest)
```bash
# Retrieve tools for a query
agent-corex retrieve "edit a file" --top-k 5 --method hybrid

# Start the API server
agent-corex start --host 0.0.0.0 --port 8000

# Check version
agent-corex version

# Check API health
agent-corex health
```

### 2. REST API
```bash
# Start the server
agent-corex start

# In another terminal, query it
curl "http://localhost:8000/retrieve_tools?query=edit file&top_k=5&method=hybrid"

# Response
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

### 3. Python Code
```python
from agent_core import rank_tools
from agent_core.tools.registry import ToolRegistry

# Create registry
registry = ToolRegistry()

# Add tools
registry.register({
    "name": "edit_file",
    "description": "Edit a file with line-based changes"
})

registry.register({
    "name": "run_tests",
    "description": "Run test suite"
})

# Retrieve relevant tools
query = "edit a file"
tools = registry.get_all_tools()
results = rank_tools(query, tools, top_k=5, method="hybrid")

# Use results
for tool in results:
    print(f"{tool['name']}: {tool['description']}")
```

### 4. With MCP Servers
```python
from agent_core.tools.mcp.mcp_loader import MCPLoader
from agent_core import rank_tools

# Load MCP servers from config
loader = MCPLoader("config/mcp.json")
manager = loader.load()

# Get all tools from MCP servers
tools = manager.get_all_tools()

# Retrieve relevant tools
results = rank_tools("your query", tools, method="hybrid")
```

---

## Ranking Methods

Agent-Core supports 3 ranking methods:

| Method | Speed | Accuracy | Use Case |
|--------|-------|----------|----------|
| **keyword** | ⚡⚡⚡ Fast | ⭐⭐ Good | Real-time, simple queries |
| **hybrid** | ⚡⚡ Medium | ⭐⭐⭐ Excellent | **Most use cases (default)** |
| **embedding** | ⚡ Slower | ⭐⭐⭐⭐ Best | Semantic search, related terms |

---

## Examples

### Example 1: Simple Tool Retrieval
```bash
python examples/basic_usage.py
```

### Example 2: MCP Server Integration
```python
from agent_core.tools.mcp.mcp_loader import MCPLoader
from agent_core import rank_tools

loader = MCPLoader("config/mcp.json")
manager = loader.load()
tools = manager.get_all_tools()

# Find tools related to file operations
file_tools = rank_tools("file operations", tools, top_k=10)
```

### Example 3: API Server
```bash
# Terminal 1: Start server
agent-corex start --host 0.0.0.0 --port 8000

# Terminal 2: Query it
for query in "edit file" "run tests" "deploy service"; do
  echo "Query: $query"
  curl "http://localhost:8000/retrieve_tools?query=$query&top_k=3"
  echo ""
done
```

---

## Configuration

### MCP Servers
Edit `config/mcp.json` to add/configure MCP servers:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
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
- Auto-cached in `.agent_corex_models/`

To use a different model, edit `packages/retrieval/embeddings.py`:
```python
self.model = SentenceTransformer(
    "sentence-transformers/all-mpnet-base-v2",  # Change here
    cache_folder=".agent_corex_models"
)
```

---

## Common Commands

```bash
# Install with optional dependencies
pip install agent-corex[redis]        # Redis support
pip install agent-corex[dev]          # Development tools
pip install agent-corex[dev,redis]    # Everything

# Run tests
pytest tests/

# Run with coverage
pytest tests/ --cov=agent_core

# Format code
black .

# Lint code
flake8 .

# Type check
mypy agent_core/
```

---

## Troubleshooting

### ImportError when importing agent_core
```bash
# Make sure it's installed
pip install -e .

# Or install from PyPI
pip install agent-corex
```

### Embedding model download fails
The model is ~80MB. If download fails:
- Check internet connection
- Try again (sometimes transient failures)
- Model will be cached after first successful download

### API server won't start
```bash
# Check if port is in use
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use different port
agent-corex start --port 8001
```

### Tests fail
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Run with verbose output
pytest tests/ -v

# Run specific test
pytest tests/test_retrieval.py::TestRanker -v
```

---

## Next Steps

- 📖 Read [README.md](README.md) for complete documentation
- 🔧 Check [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- 💻 Explore [examples/basic_usage.py](examples/basic_usage.py) for more examples
- 🧪 Run tests: `pytest tests/ -v`
- 🐛 Report issues on GitHub

---

## Performance

On a machine with 1000 tools:

| Method | Latency | Memory |
|--------|---------|--------|
| keyword | < 1ms | ~1MB |
| hybrid | 50-100ms | ~150MB |
| embedding | 50-100ms | ~150MB |

Throughput: **50+ requests/second** with single instance

---

## Support

- 📖 [Full Documentation](README.md)
- 🐛 [GitHub Issues](https://github.com/ankitpro/agent-corex/issues)
- 💬 [Discussions](https://github.com/ankitpro/agent-corex/discussions)

---

## License

MIT - See [LICENSE](LICENSE) file

---

Happy retrieving! 🎉
