"""
Basic usage example of the Agent-Core retrieval engine.

This example demonstrates how to retrieve the most relevant tools
for a given query using the keyword-based scorer and ranker.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from packages.retrieval.ranker import rank_tools
from packages.tools.registry import ToolRegistry

# Create a tool registry and register some example tools
registry = ToolRegistry()

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

# Get all registered tools
tools = registry.get_all_tools()

# Example 1: Retrieve top tools for a file editing query
print("=" * 50)
print("Query: 'edit a file'")
print("=" * 50)
result = rank_tools("edit a file", tools, top_k=2)
for i, tool in enumerate(result, 1):
    print(f"{i}. {tool['name']} - {tool['description']}")

# Example 2: Retrieve tools for a testing query
print("\n" + "=" * 50)
print("Query: 'run tests'")
print("=" * 50)
result = rank_tools("run tests", tools, top_k=3)
for i, tool in enumerate(result, 1):
    print(f"{i}. {tool['name']} - {tool['description']}")

# Example 3: Retrieve tools for a deployment query
print("\n" + "=" * 50)
print("Query: 'deploy service'")
print("=" * 50)
result = rank_tools("deploy service", tools, top_k=2)
for i, tool in enumerate(result, 1):
    print(f"{i}. {tool['name']} - {tool['description']}")

# Example 4: Query with no matching tools
print("\n" + "=" * 50)
print("Query: 'kubernetes cluster management'")
print("=" * 50)
result = rank_tools("kubernetes cluster management", tools, top_k=5)
if result:
    for i, tool in enumerate(result, 1):
        print(f"{i}. {tool['name']} - {tool['description']}")
else:
    print("No relevant tools found.")
