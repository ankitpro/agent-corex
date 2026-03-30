# Killer Feature: Self-Optimizing Tool Router

Your MCP automatically learns which tools work best for each type of query.

## Schema Caching

Instead of `agent-core-mcp inspect` every time MCP starts, use schema caching using your existing file.

## Auto MCP Installation

Add auto installation for MCP:

```bash
agent-core install github:modelcontextprotocol/servers/git
```

## Small Features to Enhance Agent-Core

### 1. Tool Ranking (BM25 / Vector Search)
Implement a tool ranking mechanism using BM25 or vector search.

### 2. Tool Permissions (RBAC)
Add role-based access control for tools.

### 3. Telemetry: Tool Usage Stats
Track and report usage statistics of tools.