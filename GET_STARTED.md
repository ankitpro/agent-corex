# 🚀 Get Started with Agent-CoreX in 5 Minutes

Agent-CoreX is now live on PyPI! Let's test it locally.

---

## Step 1: Install Agent-CoreX (1 minute)

```bash
# Create a virtual environment (optional but recommended)
python -m venv agent-corex-test
source agent-corex-test/bin/activate  # macOS/Linux
# or
agent-corex-test\Scripts\activate  # Windows

# Install from PyPI
pip install agent-corex

# Verify installation
agent-corex version
# Output: Agent-CoreX 1.0.0
```

---

## Step 2: Run the Test Script (2 minutes)

Download and run the test script:

```bash
# Run the test
python test_local.py
```

This will show you:
- ✅ Keyword ranking (fast, exact match)
- ✅ Hybrid ranking (recommended, keyword + semantic)
- ✅ Embedding ranking (pure semantic)
- ✅ Performance comparison
- ✅ Real examples

---

## Step 3: Try the CLI (1 minute)

```bash
# Simple query
agent-corex retrieve "edit a file"

# With options
agent-corex retrieve "file operations" --top-k 5 --method hybrid

# Start the API server
agent-corex start
```

---

## Step 4: Use in Python (1 minute)

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
    "name": "send_email",
    "description": "Send an email message"
})

# Get all tools
tools = registry.get_all_tools()

# Retrieve relevant tools
query = "modify a document"
results = rank_tools(query, tools, top_k=2, method="hybrid")

# Use results
for tool in results:
    print(f"- {tool['name']}: {tool['description']}")
```

---

## What You're Testing

| Method | Speed | Accuracy | Use Case |
|--------|-------|----------|----------|
| **keyword** | ⚡⚡⚡ Fast | ⭐⭐ Good | Real-time applications |
| **hybrid** | ⚡⚡ Medium | ⭐⭐⭐ Excellent | **Most use cases (default)** |
| **embedding** | ⚡ Slower | ⭐⭐⭐⭐ Best | Semantic understanding |

---

## Key Features You're Testing

1. **Tool Registration**: Add tools to a registry
2. **Keyword Matching**: Fast exact match ranking
3. **Semantic Search**: Find semantically similar tools
4. **Hybrid Ranking**: Combine keyword + semantic
5. **Graceful Fallback**: Works without embeddings

---

## Example Output

When you run `test_local.py`, you'll see something like:

```
================================================================================
 🚀 AGENT-COREX LOCAL TESTING 🚀
================================================================================

[SETUP] Creating tool registry and registering tools...
  ✓ Registered: edit_file
  ✓ Registered: write_file
  ✓ Registered: run_tests
  ...

================================================================================
TEST 1: KEYWORD RANKING (Exact match, very fast)
================================================================================

Query: 'edit a file'
Method: keyword
Speed: ⚡⚡⚡ Very Fast

📊 Results (top 3):
  1. edit_file           → Edit a file with line-based changes
  2. write_file          → Create or overwrite a file

...

✅ TESTING COMPLETE!
```

---

## Next Steps

After testing locally:

1. **Add More Tools**: Modify `test_local.py` to add your own tools
2. **Start API Server**: Run `agent-corex start` for HTTP API
3. **Integrate with LLM**: Use with Claude, GPT, etc.
4. **Connect MCP Servers**: Load tools from real MCP servers
5. **Production Deployment**: Deploy API server for your apps

---

## Troubleshooting

### "agent-corex: command not found"
```bash
# Make sure virtual environment is activated
source agent-corex-test/bin/activate  # macOS/Linux
```

### "ModuleNotFoundError: No module named 'agent_core'"
```bash
# Reinstall the package
pip install --upgrade agent-corex
```

### First embedding query is slow
This is normal! The model is downloaded (~80MB) and cached:
```bash
# First run: ~5-10 seconds (model download + inference)
# Subsequent runs: ~100-200ms (cached model)
```

---

## Learn More

- 📖 Full Docs: [README.md](README.md)
- 🧪 Complete Testing Guide: [LOCAL_TESTING_GUIDE.md](LOCAL_TESTING_GUIDE.md)
- 📦 PyPI Package: https://pypi.org/project/agent-corex/
- 💻 GitHub: https://github.com/ankitpro/agent-corex

---

## Success Criteria

✅ You're ready to use Agent-CoreX if:
- [ ] Installation successful: `agent-corex version` works
- [ ] CLI works: `agent-corex retrieve "test"` returns results
- [ ] Python import works: `from agent_core import rank_tools`
- [ ] Test script runs: `python test_local.py` shows all tests
- [ ] You understand the three ranking methods

---

Enjoy using Agent-CoreX! 🎉
