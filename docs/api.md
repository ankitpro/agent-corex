# API Reference

Complete REST API documentation for Agent-Core.

---

## Quick Start

### Start Server
```bash
pip install uvicorn
uvicorn agent_core.api.main:app --reload
```

### Test Endpoint
```bash
curl "http://localhost:8000/health"
# {"status": "ok"}
```

---

## Endpoints

### 1. GET /health
Health check endpoint.

**URL**: `/health`
**Method**: `GET`
**Authentication**: None

**Response** (200 OK):
```json
{
  "status": "ok",
  "tools_loaded": 42,
  "version": "1.0.0"
}
```

**Example**:
```bash
curl http://localhost:8000/health
```

---

### 2. GET /retrieve_tools
Retrieve top-k most relevant tools for a query.

**URL**: `/retrieve_tools`
**Method**: `GET`
**Authentication**: None

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | Required | Search query |
| `top_k` | integer | 5 | Number of results to return |
| `method` | string | hybrid | Ranking method: keyword, embedding, or hybrid |

**Response** (200 OK):
```json
[
  {
    "name": "edit_file",
    "description": "Edit file contents",
    "server": "filesystem",
    "schema": {...},
    "score": 0.95
  },
  {
    "name": "write_file",
    "description": "Write to file",
    "server": "filesystem",
    "schema": {...},
    "score": 0.87
  }
]
```

**Examples**:

```bash
# Default (hybrid ranking)
curl "http://localhost:8000/retrieve_tools?query=edit%20file"

# Custom top_k
curl "http://localhost:8000/retrieve_tools?query=edit%20file&top_k=10"

# Keyword-only (fast)
curl "http://localhost:8000/retrieve_tools?query=edit%20file&method=keyword"

# Embedding-only (semantic)
curl "http://localhost:8000/retrieve_tools?query=edit%20file&method=embedding"

# Hybrid (recommended)
curl "http://localhost:8000/retrieve_tools?query=edit%20file&method=hybrid"
```

---

### 3. GET /tools
List all available tools.

**URL**: `/tools`
**Method**: `GET`
**Authentication**: None

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Maximum results to return |
| `offset` | integer | 0 | Results to skip |

**Response** (200 OK):
```json
[
  {
    "name": "edit_file",
    "description": "Edit file contents",
    "server": "filesystem",
    "schema": {...}
  },
  {
    "name": "list_files",
    "description": "List directory contents",
    "server": "filesystem",
    "schema": {...}
  }
]
```

**Examples**:

```bash
# Get first 50 tools
curl "http://localhost:8000/tools"

# Get specific range
curl "http://localhost:8000/tools?limit=10&offset=20"

# Get all tools (use with caution)
curl "http://localhost:8000/tools?limit=10000"
```

---

### 4. GET /tools/{name}
Get details for a specific tool.

**URL**: `/tools/{name}`
**Method**: `GET`
**Authentication**: None

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Tool name |

**Response** (200 OK):
```json
{
  "name": "edit_file",
  "description": "Edit file contents with optional line selection",
  "server": "filesystem",
  "schema": {
    "type": "object",
    "properties": {
      "path": {"type": "string"},
      "content": {"type": "string"},
      "start_line": {"type": "integer"}
    },
    "required": ["path", "content"]
  }
}
```

**Response** (404 Not Found):
```json
{"error": "Tool not found"}
```

**Examples**:

```bash
# Get tool details
curl "http://localhost:8000/tools/edit_file"

# Tool not found
curl "http://localhost:8000/tools/nonexistent_tool"
```

---

### 5. POST /reload
Reload MCP configuration without restart.

**URL**: `/reload`
**Method**: `POST`
**Authentication**: None
**Body**: Empty

**Response** (200 OK):
```json
{
  "status": "reloaded",
  "tools_loaded": 42
}
```

**Response** (500 Error):
```json
{"error": "Failed to reload configuration"}
```

**Examples**:

```bash
# Reload configuration
curl -X POST "http://localhost:8000/reload"

# After updating config/mcp.json
curl -X POST "http://localhost:8000/reload"
```

---

## Ranking Methods

### Keyword Method
```
method=keyword
```
- **Speed**: < 1ms
- **Accuracy**: 70-80%
- **Use when**: Need instant results, simple queries
- **Example**: `?query=edit%20file&method=keyword`

### Embedding Method
```
method=embedding
```
- **Speed**: 50-100ms
- **Accuracy**: 90-95%
- **Use when**: Need semantic accuracy, synonyms matter
- **Example**: `?query=modify%20document&method=embedding`

### Hybrid Method (Recommended)
```
method=hybrid
```
- **Speed**: 50-100ms
- **Accuracy**: 85-92%
- **Weights**: 30% keyword + 70% embedding
- **Use when**: Best of both worlds (default)
- **Example**: `?query=edit%20file&method=hybrid`

---

## Error Handling

### Bad Request (400)
```json
{
  "error": "query parameter is required"
}
```

### Server Error (500)
```json
{
  "error": "Internal server error"
}
```

---

## Rate Limiting

Currently no rate limiting. See deployment guide for production setup.

---

## Authentication

Currently no authentication required. See deployment guide for adding API keys.

---

## Response Format

All responses are JSON:
- **Success**: Status 200, JSON body
- **Error**: Status 4xx or 5xx, JSON error object

---

## Pagination

### Using limit and offset

```bash
# Get first 20 tools
curl "http://localhost:8000/tools?limit=20&offset=0"

# Get next 20 tools
curl "http://localhost:8000/tools?limit=20&offset=20"

# Get tools 100-150
curl "http://localhost:8000/tools?limit=50&offset=100"
```

---

## Performance

### Latency Benchmarks

| Endpoint | Method | Time |
|----------|--------|------|
| /health | - | <1ms |
| /retrieve_tools | keyword | 1-5ms |
| /retrieve_tools | embedding | 80-120ms |
| /retrieve_tools | hybrid | 80-120ms |
| /tools | - | <5ms |
| /tools/{name} | - | <1ms |

### Optimization Tips

1. **Use keyword method** for real-time applications
2. **Use hybrid or embedding** for accuracy
3. **Cache results** for common queries
4. **Use reasonable top_k** (5-10 usually sufficient)
5. **Batch requests** when possible

---

## SDK Usage

### Python
```python
import requests

# Query tools
response = requests.get(
    "http://localhost:8000/retrieve_tools",
    params={"query": "edit file", "top_k": 5}
)
tools = response.json()
```

### JavaScript
```javascript
// Query tools
const response = await fetch(
  'http://localhost:8000/retrieve_tools?query=edit%20file&top_k=5'
);
const tools = await response.json();
```

### cURL
```bash
curl "http://localhost:8000/retrieve_tools?query=edit%20file&top_k=5"
```

---

## Integration Examples

### LangChain
```python
from agent_core.retrieval.ranker import rank_tools

def get_tools_for_agent(query, all_tools):
    return rank_tools(query, all_tools, top_k=10)
```

### CrewAI
```python
from agent_core.retrieval.ranker import rank_tools

# In your task or agent
relevant_tools = rank_tools(
    "user request",
    available_tools,
    top_k=5,
    method="hybrid"
)
```

### FastAPI Integration
```python
from fastapi import FastAPI
from agent_core.retrieval.ranker import rank_tools

app = FastAPI()

@app.get("/my-tools")
def get_relevant_tools(query: str):
    tools = get_all_tools()  # Your tool source
    return rank_tools(query, tools, top_k=5)
```

---

## Troubleshooting

### 404 Not Found
- Server not running: `uvicorn agent_core.api.main:app --reload`
- Wrong port: Check URL matches server port

### 500 Internal Error
- Check server logs for detailed error
- Verify MCP configuration is valid
- Ensure all dependencies are installed

### Slow Responses
- First query downloads embedding model (~30-60s)
- Use keyword method for faster results
- Check network latency
- See performance tips above

---

## Next Steps

- 📖 [Deployment Guide](deployment.md)
- 📖 [Full Tutorial](tutorial.md)
- 💬 [GitHub Issues](https://github.com/ankitpro/agent-corex/issues)

---

**Last Updated**: March 2026
**Version**: 1.0.0
