# Examples

This directory contains example scripts demonstrating Agent-Core usage.

## Files

### basic_usage.py

Simple example showing how to use the retrieval engine.

**Run:**
```bash
python examples/basic_usage.py
```

**Output:**
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

**Key Concepts:**
- Creating a tool registry
- Registering tools
- Using the ranker to retrieve relevant tools
- Testing with different queries

## Usage Patterns

### Pattern 1: Simple Tool Selection

```python
from packages.retrieval.ranker import rank_tools
from packages.tools.registry import ToolRegistry

registry = ToolRegistry()
registry.register({"name": "tool1", "description": "..."})

tools = rank_tools("query", registry.get_all_tools(), top_k=5)
```

### Pattern 2: With MCP Integration

```python
from packages.tools.mcp.mcp_loader import MCPLoader

loader = MCPLoader("config/mcp.json")
manager = loader.load()

tools = manager.get_all_tools()
results = rank_tools("query", tools)
```

### Pattern 3: With Custom Ranking

```python
from packages.retrieval.ranker import rank_tools

# Keyword-only (fast)
fast = rank_tools(query, tools, method="keyword")

# Hybrid (recommended)
balanced = rank_tools(query, tools, method="hybrid")

# Semantic (accurate)
semantic = rank_tools(query, tools, method="embedding")
```

## Common Use Cases

### 1. LLM Agent Tool Selection

```python
def select_tools_for_agent(user_query: str, available_tools: list):
    """Select the best tools for an LLM agent."""
    return rank_tools(user_query, available_tools, top_k=5, method="hybrid")
```

### 2. Command-Line Tool Discovery

```python
def find_command(description: str, commands: list):
    """Help users find relevant commands."""
    results = rank_tools(description, commands, method="semantic")
    for cmd in results:
        print(f"  {cmd['name']}: {cmd['description']}")
```

### 3. API Endpoint Routing

```python
def route_request(query: str, endpoints: list):
    """Route requests to the most relevant API endpoint."""
    endpoint = rank_tools(query, endpoints, top_k=1, method="hybrid")[0]
    return endpoint['name']
```

## Advanced Examples

### Custom Scoring

```python
from packages.retrieval.hybrid_scorer import HybridScorer

scorer = HybridScorer(keyword_weight=0.2, embedding_weight=0.8)
score = scorer.score("query", tool)
```

### Batch Processing

```python
from packages.retrieval.ranker import rank_tools

queries = [
    "edit file",
    "run tests",
    "deploy service"
]

for query in queries:
    results = rank_tools(query, tools, top_k=3)
    print(f"{query}: {[t['name'] for t in results]}")
```

### Filtering After Ranking

```python
from packages.retrieval.ranker import rank_tools

results = rank_tools(query, tools, top_k=10)

# Filter by server type
filesystem_tools = [t for t in results if t.get('server') == 'filesystem']

# Filter by availability
available = [t for t in results if t.get('available', True)]
```

## Testing Examples

Run the examples:

```bash
# Basic usage
python examples/basic_usage.py

# Or import in your code
from examples.basic_usage import SAMPLE_TOOLS
```

## Creating Your Own Example

Create a new file in `examples/`:

```python
"""
Example: Your Example Name

Description of what this example demonstrates.
"""

from packages.retrieval.ranker import rank_tools
from packages.tools.registry import ToolRegistry

# Setup
registry = ToolRegistry()
# ... register tools ...

# Example code
query = "your query"
results = rank_tools(query, registry.get_all_tools(), top_k=5)

# Display results
for tool in results:
    print(f"- {tool['name']}: {tool['description']}")
```

Then run it:
```bash
python examples/your_example.py
```
