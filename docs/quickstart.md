---
layout: page
title: ⚡ Quick Start Guide
description: Get Agent-Corex running in 5 minutes
permalink: /quickstart/
---

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

## 3. Connect Claude Desktop or Cursor (Recommended)

The fastest way to start using Agent-CoreX is to wire it into your AI client as an MCP server.

```bash
agent-corex init
```

This command:
1. Scans for Claude Desktop and Cursor on your machine
2. Shows you which MCP servers are already configured
3. **Merges** the `agent-corex` entry — your existing servers are kept untouched
4. Creates a timestamped backup before writing anything

**Example output:**

```
Scanning for AI tools...

  [+] Claude Desktop: /Users/you/Library/Application Support/Claude/claude_desktop_config.json
      Existing servers (will be kept):
        - filesystem
        - git
      Add 'agent-corex' entry in Claude Desktop? [Y/n]: Y
      [+] Added. mcpServers now contains 3 server(s):
            - agent-corex  <-- agent-corex
            - filesystem
            - git
      Backup: claude_desktop_config.20260323_120000.bak

Done. Restart the tool for changes to take effect.
```

Restart Claude Desktop or Cursor and Agent-CoreX appears as an available MCP server.

**Skip confirmation prompts:**
```bash
agent-corex init --yes
```

---

## 4. Try It — CLI

```bash
agent-corex retrieve "edit file" --top-k 3
```

**Output:**
```
Found 3 tool(s) for: 'edit file'

1. edit_file
   Edit a file with line-based changes

2. write_file
   Create or overwrite a file

3. modify_text
   Modify text content in a file
```

---

## 5. Check Your Setup

```bash
agent-corex status
```

```
agent-corex  v1.0.3

Auth
  [-] Logged in: No
    Run: agent-corex login

Config
  Path:   ~/.agent-corex/config.json
  Exists: No

MCP Clients
  [+] Claude Desktop: detected
      Config:             ~/Library/Application Support/Claude/claude_desktop_config.json
      agent-corex inject: [+] Yes

Available Tools
  Free (2):
    [+] retrieve_tools
    [+] list_mcp_servers
  Enterprise (3):
    [-] [locked] github_search
    [-] [locked] web_search
    [-] [locked] database_query

  Run  agent-corex login  to unlock enterprise tools.
```

---

## 6. Other Options

### Python Code (3 lines)
```python
from agent_core.retrieval.ranker import rank_tools

tools = [{"name": "edit_file", "description": "Edit files"}]
results = rank_tools("edit file", tools)
print(results)
```

### REST API (Run server)
```bash
agent-corex start --port 8000

# In another terminal
curl "http://localhost:8000/retrieve_tools?query=edit%20file&top_k=3"
```

---

## 7. Next Steps

### Learn More
- 📖 [MCP Setup Guide](/mcp-setup) — detailed Claude/Cursor setup
- 📖 [Full Installation Guide](/installation)
- 📖 [API Reference](/api)

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
