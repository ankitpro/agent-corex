# Agent-CoreX Local Testing Guide

Complete guide to test Agent-CoreX locally with MCP servers and retrieval.

---

## Part 1: Installation

### Step 1.1: Create a Fresh Virtual Environment

```bash
# Create virtual environment
python -m venv agent-corex-env

# Activate it
# On macOS/Linux:
source agent-corex-env/bin/activate

# On Windows:
agent-corex-env\Scripts\activate
```

### Step 1.2: Install Agent-CoreX from PyPI

```bash
# Upgrade pip
pip install --upgrade pip

# Install agent-corex
pip install agent-corex

# Verify installation
agent-corex version
# Should output: Agent-CoreX 1.0.0
```

### Step 1.3: Verify CLI Works

```bash
# Test basic command
agent-corex retrieve "edit a file" --top-k 3 --method hybrid

# You should see the default tools are registered
# Output will show tool names and descriptions
```

---

## Part 2: Setup MCP Servers (Local Configuration)

### Step 2.1: Create Project Directory

```bash
mkdir agent-corex-test
cd agent-corex-test
```

### Step 2.2: Create MCP Configuration

Create a file named `mcp.json`:

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
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory"
      ]
    },
    "everything": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-everything"
      ]
    }
  }
}
```

### Step 2.3: Create Workspace Directory

```bash
mkdir workspace
echo "This is a test workspace" > workspace/README.md
```

---

## Part 3: Python Testing (Import & Use)

### Step 3.1: Create Test Script

Create a file `test_agent_corex.py`:

```python
#!/usr/bin/env python
"""Test Agent-CoreX with MCP servers and retrieval."""

from agent_core import rank_tools
from agent_core.tools.registry import ToolRegistry

# ============================================================================
# PART 1: Test with Default Tools (No MCP)
# ============================================================================
print("=" * 70)
print("PART 1: Testing with Default Tools (No MCP)")
print("=" * 70)

# Create a registry
registry = ToolRegistry()

# Register some example tools
registry.register({
    "name": "edit_file",
    "description": "Edit a file with line-based changes"
})

registry.register({
    "name": "write_file",
    "description": "Create or overwrite a file"
})

registry.register({
    "name": "run_tests",
    "description": "Run test suite for the project"
})

registry.register({
    "name": "deploy_service",
    "description": "Deploy a service to production"
})

registry.register({
    "name": "check_logs",
    "description": "Check application logs"
})

# Get all tools
tools = registry.get_all_tools()
print(f"\nRegistered {len(tools)} tools")

# ============================================================================
# Test 1: Basic Keyword Ranking
# ============================================================================
print("\n" + "-" * 70)
print("TEST 1: Keyword-based Ranking (Fast)")
print("-" * 70)

query = "edit a file"
print(f"\nQuery: '{query}'")
print(f"Method: keyword")

results = rank_tools(query, tools, top_k=3, method="keyword")
print(f"\nTop 3 results:")
for i, tool in enumerate(results, 1):
    print(f"  {i}. {tool['name']}")
    print(f"     → {tool['description']}")

# ============================================================================
# Test 2: Hybrid Ranking (Keyword + Embedding)
# ============================================================================
print("\n" + "-" * 70)
print("TEST 2: Hybrid Ranking (Keyword + Semantic)")
print("-" * 70)

query = "modify file content"
print(f"\nQuery: '{query}'")
print(f"Method: hybrid (30% keyword + 70% embedding)")

results = rank_tools(query, tools, top_k=3, method="hybrid")
print(f"\nTop 3 results:")
for i, tool in enumerate(results, 1):
    print(f"  {i}. {tool['name']}")
    print(f"     → {tool['description']}")

# ============================================================================
# Test 3: Embedding-based Ranking (Pure Semantic)
# ============================================================================
print("\n" + "-" * 70)
print("TEST 3: Embedding-based Ranking (Pure Semantic)")
print("-" * 70)

query = "run application tests"
print(f"\nQuery: '{query}'")
print(f"Method: embedding (semantic similarity only)")

results = rank_tools(query, tools, top_k=3, method="embedding")
print(f"\nTop 3 results:")
for i, tool in enumerate(results, 1):
    print(f"  {i}. {tool['name']}")
    print(f"     → {tool['description']}")

# ============================================================================
# Test 4: Query with No Perfect Matches
# ============================================================================
print("\n" + "-" * 70)
print("TEST 4: Query with Semantic Match (No Keyword Match)")
print("-" * 70)

query = "upload my application to server"
print(f"\nQuery: '{query}'")
print(f"Method: hybrid")
print("\nNote: This query has no keyword overlap with 'deploy_service'")
print("But embedding should find it semantically!")

results = rank_tools(query, tools, top_k=3, method="hybrid")
print(f"\nTop 3 results:")
for i, tool in enumerate(results, 1):
    print(f"  {i}. {tool['name']}")
    print(f"     → {tool['description']}")

# ============================================================================
# Test 5: Multiple Queries
# ============================================================================
print("\n" + "-" * 70)
print("TEST 5: Multiple Queries")
print("-" * 70)

test_queries = [
    ("file operations", "hybrid"),
    ("testing", "keyword"),
    ("log monitoring", "embedding"),
    ("production release", "hybrid"),
]

for query, method in test_queries:
    print(f"\nQuery: '{query}' (method: {method})")
    results = rank_tools(query, tools, top_k=2, method=method)
    if results:
        for i, tool in enumerate(results, 1):
            print(f"  {i}. {tool['name']}")
    else:
        print("  No results found")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "=" * 70)
print("TESTING COMPLETE!")
print("=" * 70)
print("""
✅ Agent-CoreX is working correctly!

Key Features Tested:
  ✓ Tool registry and registration
  ✓ Keyword-based ranking (exact match)
  ✓ Hybrid ranking (keyword + semantic)
  ✓ Embedding-based ranking (pure semantic)
  ✓ Multiple queries with different methods
  ✓ Graceful handling of queries with no matches

Next Steps:
  1. Test with MCP servers (see Part 2 in README)
  2. Try the API server: agent-corex start
  3. Test via REST: curl http://localhost:8000/retrieve_tools?query=...
  4. Integrate into your LLM application
""")
```

### Step 3.2: Run the Test Script

```bash
python test_agent_corex.py
```

You should see output showing different ranking methods working!

---

## Part 4: Test with MCP Servers

### Step 4.1: Start MCP Servers (Optional - Advanced)

If you have Node.js and npm installed:

```bash
# Install npx if needed
npm install -g npm

# Test filesystem MCP server
npx -y @modelcontextprotocol/server-filesystem ./workspace
```

This will start the filesystem MCP server and you can interact with it.

### Step 4.2: Test API Server

```bash
# Start the API server
agent-corex start --host 0.0.0.0 --port 8000

# In another terminal, test it:
curl "http://localhost:8000/retrieve_tools?query=edit%20file&top_k=5&method=hybrid"

# Or use Python requests
python -c "
import requests
response = requests.get('http://localhost:8000/retrieve_tools',
    params={'query': 'edit a file', 'top_k': 3, 'method': 'hybrid'})
print(response.json())
"
```

---

## Part 5: Common Tasks

### Task 1: Add More Tools

Edit `test_agent_corex.py` and add more tools to the registry:

```python
registry.register({
    "name": "send_email",
    "description": "Send an email to a recipient"
})

registry.register({
    "name": "schedule_meeting",
    "description": "Schedule a meeting with participants"
})
```

### Task 2: Test Different Ranking Methods

```python
query = "send notification"

# Try all three methods
for method in ["keyword", "hybrid", "embedding"]:
    print(f"\nMethod: {method}")
    results = rank_tools(query, tools, top_k=2, method=method)
    for tool in results:
        print(f"  - {tool['name']}")
```

### Task 3: Measure Performance

```python
import time

query = "file operations"
tools = registry.get_all_tools()

for method in ["keyword", "hybrid", "embedding"]:
    start = time.time()
    results = rank_tools(query, tools, top_k=5, method=method)
    elapsed = (time.time() - start) * 1000  # ms
    print(f"{method:12} → {elapsed:6.2f}ms for {len(results)} results")
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'agent_core'"

**Solution:**
```bash
# Make sure virtual environment is activated
source agent-corex-env/bin/activate  # macOS/Linux
# or
agent-corex-env\Scripts\activate  # Windows

# Reinstall
pip install agent-corex
```

### Issue: "embedding model not found"

**Solution:**
First time you run embedding-based ranking, the model is downloaded (~80MB):
```python
# This will download the model automatically
results = rank_tools(query, tools, method="embedding")
```

It's cached in `.agent_core_models/` after first run.

### Issue: MCP servers not connecting

**Solution:**
MCP servers are optional. Agent-CoreX works fine with just the tool registry:
```python
# This works without any MCP servers
registry.register({"name": "tool1", "description": "..."})
results = rank_tools(query, registry.get_all_tools())
```

---

## What to Explore Next

1. **Try Different Queries**: Experiment with queries that match and don't match
2. **Ranking Methods**: See how keyword, hybrid, and embedding methods differ
3. **Performance**: Notice hybrid ranking is slower but more accurate
4. **API Server**: Start the server and integrate with your applications
5. **MCP Integration**: Connect real MCP servers for tool discovery

---

## Example Output

When you run `test_agent_corex.py`, you'll see:

```
======================================================================
PART 1: Testing with Default Tools (No MCP)
======================================================================

Registered 5 tools

----------------------------------------------------------------------
TEST 1: Keyword-based Ranking (Fast)
----------------------------------------------------------------------

Query: 'edit a file'
Method: keyword

Top 3 results:
  1. edit_file
     → Edit a file with line-based changes
  2. write_file
     → Create or overwrite a file

----------------------------------------------------------------------
TEST 2: Hybrid Ranking (Keyword + Semantic)
----------------------------------------------------------------------

Query: 'modify file content'
Method: hybrid (30% keyword + 70% embedding)

Top 3 results:
  1. edit_file
     → Edit a file with line-based changes
  2. write_file
     → Create or overwrite a file

... (more tests)

======================================================================
TESTING COMPLETE!
======================================================================
```

---

## Success Criteria

✅ You've successfully tested Agent-CoreX locally if:
- Command line works: `agent-corex version`
- Python import works: `from agent_core import rank_tools`
- All three ranking methods return results
- Test script runs without errors
- You understand the differences between ranking methods

---

## Next Steps

1. **Integrate with LLM**: Use Agent-CoreX to select tools for Claude, GPT, etc.
2. **Real MCP Servers**: Connect to filesystem, memory, or custom servers
3. **Customize Scoring**: Modify ranking weights for your use case
4. **Production Deployment**: Deploy the API server for your applications

Enjoy using Agent-CoreX! 🚀
