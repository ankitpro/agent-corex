# Quick Start Guide (5 Minutes)

Get Agent-Core running in 5 minutes!

---

## 1. Install (1 minute)

### From PyPI (Recommended)
```bash
pip install agent-corex
```

### From Source
```bash
git clone https://github.com/ankitpro/agent-corex.git
cd agent-corex
pip install -e .
```

---

## 2. Verify Installation (1 minute)

Check that Agent-Core is installed:

```bash
agent-corex --version
# Output: agent-corex 1.0.0
```

---

## 3. Try It (1 minute)

### Option A: Command Line (Easiest)
```bash
agent-corex retrieve "edit file" --top-k 3
```

**Output:**
```json
[
  {
    "name": "edit_file",
    "description": "Edit file contents",
    "score": 0.95
  },
  {
    "name": "write_file",
    "description": "Write to file",
    "score": 0.87
  },
  {
    "name": "modify_text",
    "description": "Modify text in file",
    "score": 0.82
  }
]
```

### Option B: Python Code (3 lines)
```python
from agent_core.retrieval.ranker import rank_tools

tools = [{"name": "edit_file", "description": "Edit files"}]
results = rank_tools("edit file", tools)
print(results)
```

### Option C: REST API (Run server)
```bash
# Install dependencies
pip install uvicorn fastapi

# Start server
uvicorn agent_core.api.main:app --reload

# In another terminal
curl "http://localhost:8000/retrieve_tools?query=edit%20file&top_k=3"
```

---

## 4. Next Steps (2 minutes)

### Learn More
- 📖 [Full Installation Guide](installation.md)
- 📖 [Complete Tutorial](tutorial.md)
- 📖 [API Reference](api.md)
- 📖 [MCP Setup Guide](../MCP_SETUP_GUIDE.md)

### Try Examples
```bash
python examples/basic_usage.py
```

### Run Tests
```bash
pytest tests/ -v
```

---

## Common Issues

### "command not found: agent-corex"
Solution: Ensure installation path is in PATH
```bash
python -m agent_core.cli.main retrieve "test"
```

### "ModuleNotFoundError: No module named 'agent_core'"
Solution: Reinstall package
```bash
pip uninstall agent-corex
pip install agent-corex
```

### "CUDA not available" (Warning is OK)
This is normal. Agent-Core works fine with CPU.

---

## What's Next?

- ✅ Agent-Core is installed and working
- 📖 Read [Installation Guide](installation.md) for detailed setup
- 📖 Read [Tutorial](tutorial.md) for comprehensive usage
- 🚀 [Deploy to production](deployment.md) when ready

---

**Time taken**: ~5 minutes
**Status**: Ready to use! 🎉
