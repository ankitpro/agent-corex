# Agent-Core API

FastAPI-based REST API for the Agent-Core retrieval engine.

## Running the Server

### Basic Usage

```bash
# Make sure you're in the project root
pip install uvicorn

# Start the server
uvicorn apps.api.main:app --reload
```

API will be available at `http://localhost:8000`

**Swagger documentation:** http://localhost:8000/docs
**ReDoc documentation:** http://localhost:8000/redoc

### With Custom MCP Config

```bash
# Use a custom MCP configuration file
export MCP_CONFIG=/path/to/your/mcp.json
uvicorn apps.api.main:app --reload
```

### Production Deployment

```bash
# Use gunicorn for production
pip install gunicorn
gunicorn apps.api.main:app -w 4 -b 0.0.0.0:8000
```

## Endpoints

### Health Check

**GET** `/health`

Check if the API is running and how many tools are loaded.

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "ok",
  "tools_loaded": 42,
  "version": "1.0.0"
}
```

---

### List All Tools

**GET** `/tools`

Get a list of all available tools.

**Query Parameters:**
- `limit` (integer, optional, default: 100): Maximum number of tools to return

```bash
# Get all tools (up to 100)
curl "http://localhost:8000/tools"

# Get first 10 tools
curl "http://localhost:8000/tools?limit=10"
```

Response:
```json
[
  {
    "name": "edit_file",
    "description": "Edit a file with line-based changes",
    "server": "local"
  },
  {
    "name": "write_file",
    "description": "Create or overwrite a file",
    "server": "local"
  }
]
```

---

### Get Specific Tool

**GET** `/tools/{tool_name}`

Get details for a specific tool by name.

```bash
curl "http://localhost:8000/tools/edit_file"
```

Response:
```json
{
  "name": "edit_file",
  "description": "Edit a file with line-based changes",
  "server": "local"
}
```

If tool not found:
```json
{"detail": "Tool 'nonexistent' not found"}
```

---

### Reload Tools

**POST** `/reload`

Reload tools from configuration files. Useful after updating `config/mcp.json` or changing `MCP_CONFIG` environment variable.

```bash
curl -X POST http://localhost:8000/reload
```

Response:
```json
{
  "status": "reloaded",
  "tools_loaded": 42,
  "message": "Successfully loaded 42 tools"
}
```

---

### Retrieve Tools

**GET** `/retrieve_tools`

Retrieve the most relevant tools for a given query.

**Query Parameters:**
- `query` (string, required): The search query describing what you need
- `top_k` (integer, optional, default: 5): Number of results to return
- `method` (string, optional, default: "hybrid"): Ranking method
  - `"keyword"`: Fast keyword-only matching
  - `"hybrid"`: Recommended, combines keyword + semantic
  - `"embedding"`: Pure semantic similarity

**Example Requests:**

```bash
# Default (hybrid ranking, top 5)
curl "http://localhost:8000/retrieve_tools?query=edit file"

# With custom top_k
curl "http://localhost:8000/retrieve_tools?query=edit file&top_k=10"

# Keyword-only (fast)
curl "http://localhost:8000/retrieve_tools?query=edit file&method=keyword"

# Pure semantic
curl "http://localhost:8000/retrieve_tools?query=edit file&method=embedding"
```

**Response:**
```json
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

**Status Codes:**
- `200 OK`: Successfully retrieved tools
- `400 Bad Request`: Invalid query or method
- `500 Internal Server Error`: Server error

---

## Query Examples

### Simple Queries
```bash
# Find file operations
curl "http://localhost:8000/retrieve_tools?query=file operations"

# Find testing tools
curl "http://localhost:8000/retrieve_tools?query=run tests"

# Find deployment tools
curl "http://localhost:8000/retrieve_tools?query=deploy service"
```

### Semantic Queries (catches related tools)
```bash
# "modify" is semantically similar to "edit"
curl "http://localhost:8000/retrieve_tools?query=modify file"

# "create" is semantically similar to "write"
curl "http://localhost:8000/retrieve_tools?query=create file"

# "execute" is semantically similar to "run"
curl "http://localhost:8000/retrieve_tools?query=execute tests"
```

### Complex Queries
```bash
# Multi-word queries
curl "http://localhost:8000/retrieve_tools?query=edit and save file to disk"

# Describe your intent
curl "http://localhost:8000/retrieve_tools?query=i need to modify a file"
```

---

## Performance Tuning

### Latency vs Accuracy

**Fast (< 10ms latency):**
```bash
curl "http://localhost:8000/retrieve_tools?query=edit&method=keyword&top_k=3"
```

**Balanced (50-100ms latency):**
```bash
curl "http://localhost:8000/retrieve_tools?query=edit&method=hybrid&top_k=5"
```

**Accurate (100-200ms latency):**
```bash
curl "http://localhost:8000/retrieve_tools?query=edit&method=embedding&top_k=10"
```

### Top-K Selection

- `top_k=3`: Quick results (low latency)
- `top_k=5`: Balanced (default)
- `top_k=10`: Comprehensive results
- `top_k=20`: Complete set (higher latency)

---

## Integration Examples

### Python Requests

```python
import requests

response = requests.get(
    "http://localhost:8000/retrieve_tools",
    params={
        "query": "edit a file",
        "top_k": 5,
        "method": "hybrid"
    }
)

tools = response.json()
for tool in tools:
    print(f"- {tool['name']}: {tool['description']}")
```

### JavaScript Fetch

```javascript
const query = "edit a file";
const response = await fetch(
  `http://localhost:8000/retrieve_tools?query=${encodeURIComponent(query)}&top_k=5&method=hybrid`
);
const tools = await response.json();
tools.forEach(tool => {
  console.log(`- ${tool.name}: ${tool.description}`);
});
```

### cURL with jq

```bash
curl "http://localhost:8000/retrieve_tools?query=edit file&top_k=5" | jq '.[] | "\(.name): \(.description)"'
```

---

## Error Handling

### Invalid Query Parameter

```bash
curl "http://localhost:8000/retrieve_tools?query=&top_k=5"
```

Response (400):
```json
{"detail": "Query parameter cannot be empty"}
```

### Invalid Method

```bash
curl "http://localhost:8000/retrieve_tools?query=edit&method=invalid"
```

Response (400):
```json
{"detail": "Invalid ranking method: invalid"}
```

### Server Error

Response (500):
```json
{"detail": "Internal server error"}
```

---

## Configuration

### MCP Servers Configuration

Agent-CoreX automatically loads tools from MCP servers defined in your configuration file.

#### Default Location

By default, Agent-CoreX looks for MCP configuration at `config/mcp.json`:

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
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

#### Custom Location

Use the `MCP_CONFIG` environment variable to specify a custom config file:

```bash
export MCP_CONFIG=/path/to/your/mcp.json
uvicorn apps.api.main:app --reload
```

#### Adding MCP Servers

Edit your MCP configuration file to add more servers:

```json
{
  "mcpServers": {
    "filesystem": { /* ... */ },
    "memory": { /* ... */ },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git"]
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

Then reload the tools:

```bash
curl -X POST http://localhost:8000/reload
```

Check what tools were loaded:

```bash
curl http://localhost:8000/health
```

### Uvicorn Configuration

```bash
# Port
export UVICORN_PORT=8000

# Host
export UVICORN_HOST=0.0.0.0

# Reload
export UVICORN_RELOAD=true
```

### Command Line Options

```bash
# Custom port
uvicorn apps.api.main:app --port 8080

# Custom host
uvicorn apps.api.main:app --host 0.0.0.0

# Production mode (no reload)
uvicorn apps.api.main:app --reload false
```

---

## Monitoring

### Health Check Endpoint

```bash
# Use for load balancer health checks
curl -I http://localhost:8000/health
```

### API Documentation

Swagger UI is available at: `http://localhost:8000/docs`
ReDoc is available at: `http://localhost:8000/redoc`

---

## Scaling

### Single Instance

```bash
uvicorn apps.api.main:app --reload
```

### Multiple Workers

```bash
uvicorn apps.api.main:app --workers 4
```

### With Gunicorn

```bash
pip install gunicorn
gunicorn apps.api.main:app -w 4 -b 0.0.0.0:8000
```

### Docker

```bash
docker build -t agent-corex .
docker run -p 8000:8000 agent-corex
```

---

## Testing the API

```bash
# Test health
curl http://localhost:8000/health

# Test retrieval
curl "http://localhost:8000/retrieve_tools?query=test&top_k=3"

# Test different methods
curl "http://localhost:8000/retrieve_tools?query=test&method=keyword"
curl "http://localhost:8000/retrieve_tools?query=test&method=hybrid"
curl "http://localhost:8000/retrieve_tools?query=test&method=embedding"
```

---

## Troubleshooting

### Port Already in Use

```bash
# Use a different port
uvicorn apps.api.main:app --port 8001
```

### Model Loading Slow

First load is slow (30-60 seconds) because the embedding model is being downloaded and cached.

Subsequent requests are fast (50-100ms).

### Memory Usage

The embedding model uses ~150MB of memory. Ensure your server has at least 500MB available.

---

## Future Enhancements

- [ ] WebSocket support for streaming results
- [ ] Batch API for multiple queries
- [ ] Request/response caching
- [ ] Authentication and API keys
- [ ] Rate limiting
- [ ] Custom endpoint for tool registration
- [ ] OpenAPI/Swagger schema generation
