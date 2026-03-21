# 🚀 Agent-Core — Claude Code Task Plan

---

# 🧩 Phase 1 — Core OSS (Retrieval Engine + MCP Integration)

---

## 🧱 Task 1 — Setup Project Structure

**Prompt to Claude:**

```
Create a Python project structure for a package called "agent_core" with the following structure:

agent-core/
├── apps/api/
│   └── main.py
├── packages/
│   ├── retrieval/
│   │   ├── scorer.py
│   │   └── ranker.py
│   ├── tools/
│   │   ├── registry.py
│   │   └── mcp/
│   │       ├── mcp_client.py
│   │       ├── mcp_loader.py
│   │       └── mcp_manager.py
├── config/
│   └── mcp_config.json
├── tests/
│   ├── test_retrieval.py
│   └── test_mcp.py
├── requirements.txt

Include __init__.py files where necessary.
```

---

## 🧠 Task 2 — Implement Retrieval Engine (Scoring)

```
Implement a simple keyword-based scoring function in scorer.py.

Requirements:
- Tokenize query and tool text
- Compute overlap score
- Return float score
- Handle empty inputs safely
```

---

## 🧠 Task 3 — Implement Ranking Logic

```
In ranker.py, implement a function:

rank_tools(query: str, tools: list, top_k: int)

Requirements:
- Use scorer to score each tool
- Sort tools by score descending
- Filter out zero-score tools
- Return top_k results
```

---

## 🧩 Task 4 — Tool Registry

```
Create a ToolRegistry class that:
- Stores tools in memory
- Has method load_from_mcp(manager)
- Has method get_all_tools()

Tools should follow schema:
{
  "name": str,
  "description": str,
  "server": str
}
```

---

## 🔌 Task 5 — MCP Client

```
Implement MCPClient with:

- start() → starts subprocess
- initialize() → JSON-RPC initialize handshake
- list_tools() → calls "tools/list"

Requirements:
- Use subprocess.Popen
- Communicate via stdin/stdout
- Handle blocking reads safely
- No tool execution methods
```

---

## 🔌 Task 6 — MCP Loader

```
Implement MCPLoader:

- Read config from JSON file
- For each server:
  - create MCPClient
  - start + initialize
- Return list of clients

Do NOT include:
- caching
- indexing
- YAML support
```

---

## 🔌 Task 7 — MCP Manager

```
Implement MCPManager:

- Accept list of clients
- Method get_all_tools():
    - call list_tools() on each client
    - normalize tool schema
    - return merged list

Handle:
- failed servers gracefully
```

---

## 🌐 Task 8 — API Layer

```
Build FastAPI app with:

Endpoint: GET /retrieve_tools
Params:
- query (str)
- top_k (int, default 5)

Flow:
- load tools from registry
- rank tools
- return result

Add /health endpoint
```

---

## ⚙️ Task 9 — MCP Config

```
Create config/mcp_config.json with example:

{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./workspace"]
    }
  }
}
```

---

## 🧪 Task 10 — Tests

```
Write pytest tests for:

1. Retrieval:
- correct ranking
- top_k limit
- irrelevant query

2. MCP:
- load clients
- fetch tools
- non-empty result
```

---

## ▶️ Task 11 — Run Instructions

```
Add instructions to run:

- pip install -r requirements.txt
- uvicorn apps.api.main:app --reload
- pytest tests/
```

---

# 🚀 Phase 2 — Hosted API + Monetization Layer

---

## 🔐 Task 12 — API Key Authentication

```
Add API key middleware:

- Read API key from header
- Validate against in-memory list (for now)
- Reject unauthorized requests
```

---

## 📊 Task 13 — Usage Tracking

```
Track:
- number of queries per API key

Store in memory dict:
{
  api_key: count
}
```

---

## ⛔ Task 14 — Rate Limiting

```
Add simple rate limit:

- max queries per minute per API key
- return 429 if exceeded
```

---

## 💾 Task 15 — Optional Redis Integration

```
Add optional Redis support for:

- caching tool lists
- storing usage counters

Fallback to in-memory if Redis not available
```

---

# 🧠 Phase 3 — Intelligent Ranking (Premium Layer)

---

## 🧬 Task 16 — Embedding-Based Scoring

```
Integrate sentence-transformers:

- generate embeddings for tools
- generate embedding for query
- compute cosine similarity

Fallback to keyword scoring if model unavailable
```

---

## 🧠 Task 17 — Hybrid Ranking

```
Combine:
- keyword score
- embedding score

Weighted scoring:
final_score = 0.5 * keyword + 0.5 * embedding
```

---

## 💰 Task 18 — Premium Feature Flag

```
Enable embedding-based ranking only for:
- premium API keys

Free users use keyword-only ranking
```

---

# 🧩 Phase 4 — MCP Wrapper (User Integration)

---

## 🔌 Task 19 — MCP Wrapper Server

```
Build MCP server exposing:

Tool:
- router_search

Behavior:
- accepts query
- calls your hosted API
- returns top tools
```

---

## 🔐 Task 20 — API Key via Env

```
Read API key from environment variable:

AGENT_CORE_API_KEY

Attach to API requests
```

---

# 🧰 Phase 5 — CLI Tool

---

## ⚙️ Task 21 — CLI Setup

```
Create CLI:

agent-core retrieve "query"

Calls API and prints tools
```

---

## 📦 Task 22 — MCP Install Command

```
Add CLI command:

agent-core install <mcp_name>

For now:
- just update config file
```

---

# 🌐 Phase 6 — Basic Dashboard (Optional Early UI)

---

## 🧑‍💻 Task 23 — Simple UI

```
Build minimal UI:

- input query
- show top tools

Use simple frontend (optional)
```

---

# 🏢 Phase 7 — Enterprise Features (Later)

---

## 🔒 Task 24 — Private MCP Support

```
Allow users to:
- register custom MCP servers
- fetch tools securely
```

---

## 📊 Task 25 — Analytics

```
Track:
- most used tools
- success rate (future)
```

---

# 🎯 Final Goal

---

By the end of execution, you will have:

* ✅ OSS retrieval engine
* ✅ MCP integration
* ✅ Hosted API
* ✅ Monetization hooks
* ✅ Premium intelligence layer
* ✅ CLI + MCP wrapper

---

# 🚀 Execution Strategy

Run tasks in order:

```
Phase 1 → Phase 2 → Phase 3 → Phase 4
```

Do NOT skip ahead.

---

# 💥 Key Reminder

Stay focused on:

> 🔥 Tool Retrieval = Core Product

NOT:

* agent frameworks
* execution engines
* orchestration systems

---

# 🧾 End of Plan
