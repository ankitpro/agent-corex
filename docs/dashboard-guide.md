---
layout: page
title: 🎛️ Dashboard & Local Connection Guide
description: Connect your local Agent-Corex backend to the dashboard and test tool retrieval
permalink: /dashboard-guide/
---

# Dashboard & Local Connection Guide

The Agent-Corex Dashboard is a web-based UI that allows you to connect to a locally running Agent-Corex backend and test the tool retrieval functionality in real-time.

---

## 🚀 Quick Start

### 1. Start the Backend

```bash
# Clone and setup
git clone https://github.com/ankitpro/agent-corex.git
cd agent-corex
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .

# Start the API server
uvicorn agent_core.api.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 2. Access the Dashboard

Open your browser and navigate to:
```
https://ankitpro.github.io/agent-corex/dashboard/
```

### 3. Connect to Backend

1. **Enter Base URL**: `http://localhost:8000` (default)
2. **Click "Test Connection"**
3. **Wait for confirmation**: Should show "Connected" with server info

### 4. Query Tools

1. **Enter a search query**: "edit file", "run tests", etc.
2. **Set options**:
   - `Top K Results`: How many results to return (1-20)
   - `Ranking Method`: keyword, hybrid, or embedding
3. **Click "Search"**
4. **View results**: Tools ranked by relevance with scores

---

## 🔌 API Client Implementation

### How It Works

The dashboard uses a reusable `AgentCorexClient` class that:
1. Reads the base URL from localStorage
2. Makes fetch requests to the backend
3. Handles errors gracefully (network, CORS, HTTP)
4. Returns parsed JSON responses

### Using the API Client

```javascript
// Create a client
const client = new AgentCorexClient('http://localhost:8000');

// Test connection
const health = await client.health();
// Returns: { status: "ok", version: "1.0.2", tools_loaded: 3, ... }

// Retrieve tools
const results = await client.retrieveTools(
    'edit file',    // query
    5,              // top_k
    'hybrid'        // method: 'keyword', 'hybrid', 'embedding'
);
// Returns: Array of tools ranked by relevance
```

### Error Handling

```javascript
try {
    const results = await client.retrieveTools('edit file', 5, 'hybrid');
} catch (error) {
    if (error.type === 'NETWORK_ERROR') {
        console.error('Backend not reachable:', error.message);
    } else if (error.type === 'HTTP_ERROR') {
        console.error('API error:', error.message);
    }
}
```

---

## 💾 LocalStorage Integration

### Automatic Persistence

The dashboard automatically stores the backend URL in your browser's localStorage:

```javascript
// Save URL
Storage.setBaseUrl('http://localhost:8000');

// Retrieve URL
const baseUrl = Storage.getBaseUrl();

// Clear stored URL
Storage.clear();
```

**Benefits:**
- ✅ Don't need to re-enter URL on page reload
- ✅ Switch between different backend instances
- ✅ Works offline (URL persists)

---

## 🔐 CORS Configuration

### Backend Setup

The Agent-Corex backend is pre-configured with CORS support:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

This allows requests from:
- ✅ Local development (http://localhost:3000, etc.)
- ✅ GitHub Pages (https://ankitpro.github.io)
- ✅ Any other domain

### Troubleshooting CORS Issues

If you get a CORS error:

1. **Verify backend is running**: Check http://localhost:8000/health in browser
2. **Check CORS headers**: Backend should return `Access-Control-Allow-Origin: *`
3. **Check browser console**: For detailed CORS error messages
4. **Try different port**: If 8000 is in use, start backend on different port:
   ```bash
   uvicorn agent_core.api.main:app --port 8001
   ```

---

## 🛠️ /health Endpoint

### Purpose

The `/health` endpoint is used to verify backend connectivity and get server information.

### Response Format

```json
{
    "status": "ok",
    "version": "1.0.2",
    "tools_loaded": 3,
    "message": "Agent-Corex API is running"
}
```

### Fields

| Field | Description |
|-------|-------------|
| `status` | Server status: "ok" = running |
| `version` | API version (matches pyproject.toml) |
| `tools_loaded` | Number of tools in registry |
| `message` | Human-readable status message |

### Curl Example

```bash
# Test health endpoint
curl http://localhost:8000/health

# Response
{
    "status": "ok",
    "version": "1.0.2",
    "tools_loaded": 3,
    "message": "Agent-Corex API is running"
}
```

---

## 📱 Dashboard Features

### Connection Settings

- **Base URL Input**: Specify backend location
- **Test Connection Button**: Verify backend is accessible
- **Status Indicator**: Visual feedback (Connected/Disconnected/Testing)
- **Connection Details**: Server info, version, tools loaded
- **Clear Settings**: Reset to defaults

### Query Tools Section

- **Search Query**: Natural language query
- **Top K Results**: Limit number of results
- **Ranking Method**: Choose scoring algorithm
- **Results Display**: Tools sorted by relevance score

### Error Handling

The dashboard gracefully handles:

| Error | Message | Solution |
|-------|---------|----------|
| Network Error | Backend not reachable | Start backend with `uvicorn` |
| Invalid URL | URL format error | Use format: `http://localhost:8000` |
| CORS Error | Origin not allowed | Check backend CORS config |
| HTTP Error | 404/500 status | Check backend logs |

---

## 🎨 UI Components

### Connection Status Indicator

```
🟢 Connected
Status and server details shown below

Details:
{
  "status": "ok",
  "version": "1.0.2",
  ...
}
```

### Search Results

```
✓ Edit File
  Edit a file with line-based changes
  Score: 0.9542

✓ Write File
  Create or overwrite a file
  Score: 0.8765
```

### Error Messages

```
⚠️ Connection Failed
Network Error: Make sure the backend is running at http://localhost:8000

To start the backend:
uvicorn agent_core.api.main:app --reload
```

---

## 🔄 Ranking Methods

### Keyword Method

- **Speed**: <1ms
- **Accuracy**: ⭐⭐
- **Best For**: Quick filtering, simple queries
- **Algorithm**: BM25 term matching

### Hybrid Method (Recommended)

- **Speed**: 50-100ms
- **Accuracy**: ⭐⭐⭐
- **Best For**: Balanced speed/accuracy
- **Algorithm**: 30% keyword + 70% semantic

### Embedding Method

- **Speed**: 50-100ms
- **Accuracy**: ⭐⭐⭐⭐
- **Best For**: Semantic accuracy, complex queries
- **Algorithm**: sentence-transformers + cosine similarity

---

## 📱 Integration Examples

### React Component

```jsx
// Custom hook for Agent-Corex
function useAgentCorex() {
    const [client, setClient] = useState(null);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        const baseUrl = localStorage.getItem('agent_corex_base_url')
            || 'http://localhost:8000';
        const newClient = new AgentCorexClient(baseUrl);
        setClient(newClient);

        newClient.health()
            .then(() => setConnected(true))
            .catch(() => setConnected(false));
    }, []);

    return { client, connected };
}

// Usage
function MyComponent() {
    const { client, connected } = useAgentCorex();

    const search = async (query) => {
        if (!client) return;
        try {
            const results = await client.retrieveTools(query, 5, 'hybrid');
            console.log(results);
        } catch (error) {
            console.error('Search failed:', error);
        }
    };

    return (
        <div>
            Status: {connected ? 'Connected' : 'Disconnected'}
            <button onClick={() => search('edit file')}>Search</button>
        </div>
    );
}
```

### Vue Component

```vue
<template>
    <div>
        <p>Status: {{ connected ? 'Connected' : 'Disconnected' }}</p>
        <input v-model="query" placeholder="Search query">
        <button @click="search">Search</button>
        <div v-for="tool in results" :key="tool.name">
            <strong>{{ tool.name }}</strong>: {{ tool.description }}
            <small>Score: {{ tool.score.toFixed(4) }}</small>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            client: null,
            connected: false,
            query: '',
            results: []
        };
    },
    mounted() {
        const baseUrl = localStorage.getItem('agent_corex_base_url')
            || 'http://localhost:8000';
        this.client = new AgentCorexClient(baseUrl);

        this.client.health()
            .then(() => this.connected = true)
            .catch(() => this.connected = false);
    },
    methods: {
        async search() {
            try {
                this.results = await this.client.retrieveTools(
                    this.query, 5, 'hybrid'
                );
            } catch (error) {
                console.error('Search failed:', error);
            }
        }
    }
};
</script>
```

---

## 🚀 Advanced Usage

### Connect to Remote Backend

Instead of localhost, you can connect to any URL:

```
Base URL: https://api.example.com
```

**Requirements:**
- ✅ Backend must have CORS enabled
- ✅ HTTPS recommended for remote connections
- ✅ Backend must be accessible from your location

### Running Multiple Instances

Start multiple backends on different ports:

```bash
# Terminal 1
uvicorn agent_core.api.main:app --port 8000

# Terminal 2
uvicorn agent_core.api.main:app --port 8001

# Terminal 3
uvicorn agent_core.api.main:app --port 8002
```

Then switch between them in the dashboard:
- `http://localhost:8000`
- `http://localhost:8001`
- `http://localhost:8002`

---

## 📚 Troubleshooting

### "Connection Failed: Network Error"

**Cause**: Backend is not running

**Solution**:
```bash
uvicorn agent_core.api.main:app --reload
```

### "Connection Failed: CORS Error"

**Cause**: Backend CORS not properly configured

**Solution**: Verify CORS middleware in backend:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### "Search Failed: HTTP 404"

**Cause**: `/retrieve_tools` endpoint not found

**Solution**: Verify backend version is 1.0.2+:
```bash
curl http://localhost:8000/health
```

### "Search Failed: No Results"

**Cause**: No tools registered in backend

**Solution**: Check tool registry in backend:
```python
tools = tool_registry.get_all_tools()
print(f"Tools loaded: {len(tools)}")
```

---

## 🔗 Related Documentation

- **[Quick Start](/quickstart/)** - 5-minute setup
- **[API Reference](/api/)** - Full API documentation
- **[Installation](/installation/)** - Installation guide
- **[Deployment](/deployment/)** - Production deployment

---

**Last Updated**: March 22, 2026
**Version**: 1.0.2+
**Status**: ✅ Ready for use
