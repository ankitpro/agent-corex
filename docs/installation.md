---
layout: page
title: 📦 Installation Guide
description: Complete setup instructions for Agent-Corex
permalink: /installation/
---

# Installation Guide

Complete setup instructions for Agent-Core.

---

## Requirements

- **Python**: 3.8 or higher
- **pip**: Latest version
- **OS**: Linux, macOS, or Windows
- **RAM**: 2GB minimum (150MB with embeddings model)
- **Disk**: 500MB for dependencies + 80MB for embedding model

---

## Installation Methods

### Method 1: PyPI (Recommended)

**Easiest and fastest way to install:**

```bash
pip install agent-corex
```

Verify:
```bash
agent-corex --version
# Output: agent-corex 1.0.0
```

**Time**: ~30 seconds

---

### Method 2: From Source

**For development or testing:**

```bash
# Clone repository
git clone https://github.com/ankitpro/agent-corex.git
cd agent-corex

# Install in development mode
pip install -e .

# Verify
agent-corex --version
```

**Time**: ~2 minutes

---

### Method 3: Docker

**For containerized deployment:**

```bash
# Build image
docker build -t agent-corex .

# Run container
docker run -p 8000:8000 agent-corex

# Access API
curl http://localhost:8000/health
```

**Time**: ~3 minutes

---

### Method 4: Conda

**For conda environments:**

```bash
conda create -n agent-corex python=3.10
conda activate agent-corex
pip install agent-corex
```

**Time**: ~1 minute

---

## Verify Installation

### Check Version
```bash
agent-corex --version
# Output: agent-corex 1.0.0
```

### Check Health
```bash
agent-corex health
# Output: {"status": "ok", "tools_loaded": 0}
```

### Run First Query
```bash
agent-corex retrieve "edit file" --top-k 3
# Output: JSON with tool results
```

---

## Connect to Claude Desktop or Cursor

After installing, wire Agent-CoreX into your AI client with one command:

```bash
agent-corex init
```

### What it does

| Step | Action |
|------|--------|
| 1 | Scans for Claude Desktop and Cursor on your system |
| 2 | Shows existing MCP servers that will be preserved |
| 3 | Creates a timestamped backup of the config file |
| 4 | **Merges** the `agent-corex` entry into `mcpServers` |
| 5 | Leaves all other servers and settings untouched |

### Skip prompts

```bash
agent-corex init --yes
```

### Result — what gets added to the config

```json
{
  "mcpServers": {
    "agent-corex": {
      "command": "agent-corex",
      "args": ["serve"]
    }
  }
}
```

Any existing `mcpServers` entries (e.g. `filesystem`, `git`) remain in the file.
A backup is always saved before any write, e.g. `claude_desktop_config.20260323_120000.bak`.

### Verify

```bash
agent-corex status
```

### Where config files live

| Tool | Platform | Path |
|------|----------|------|
| Claude Desktop | Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Desktop | macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop | Linux | `~/.config/Claude/claude_desktop_config.json` |
| Cursor | Windows | `%APPDATA%\Cursor\User\mcp.json` |
| Cursor | macOS | `~/Library/Application Support/Cursor/User/mcp.json` |
| Cursor | Linux | `~/.config/Cursor/User/mcp.json` |

**[Full MCP setup guide →](/mcp-setup)**

---

## First-Run Setup

The first time you use embedding-based ranking, the system downloads a model (~80MB):

```bash
agent-corex retrieve "test" --method embedding
# On first run: Downloading model... (30-60 seconds)
# On subsequent runs: Uses cached model (instant)
```

**Where models are cached**: `~/.cache/agent_core_models/`

---

## Optional Dependencies

### For FastAPI Server
```bash
pip install uvicorn fastapi
uvicorn agent_core.api.main:app --reload
```

### For Advanced Features
```bash
# Redis support
pip install redis

# PostgreSQL support
pip install psycopg2-binary

# For development
pip install pytest pytest-cov black flake8 mypy
```

---

## Troubleshooting

### Issue: "pip: command not found"
**Solution**: Ensure Python is properly installed
```bash
python -m pip install agent-corex
```

### Issue: "agent-corex: command not found"
**Solution**: Ensure scripts are in PATH
```bash
# Reinstall
pip uninstall agent-corex
pip install agent-corex

# Or use module directly
python -m agent_core.cli.main retrieve "test"
```

### Issue: Permission denied
**Solution**: Use --user flag or virtual environment
```bash
pip install --user agent-corex
# OR
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
pip install agent-corex
```

### Issue: CUDA not available warning
**Solution**: This is normal, CPU works fine
```bash
# CPU only is supported and sufficient
agent-corex retrieve "test"
```

### Issue: Slow on first query
**Solution**: Model download takes 30-60s on first run
```bash
# First query (includes model download)
agent-corex retrieve "test"  # 30-60 seconds

# Subsequent queries
agent-corex retrieve "test"  # <100ms
```

---

## Virtual Environment Setup (Recommended)

### Using venv
```bash
# Create environment
python -m venv agent-core-env

# Activate
# On Linux/macOS:
source agent-core-env/bin/activate
# On Windows:
agent-core-env\Scripts\activate

# Install agent-corex
pip install agent-corex

# Deactivate when done
deactivate
```

### Using conda
```bash
# Create environment
conda create -n agent-corex python=3.10

# Activate
conda activate agent-corex

# Install agent-corex
pip install agent-corex

# Deactivate when done
conda deactivate
```

---

## Docker Setup

### Build Docker Image
```bash
# Build
docker build -t agent-corex:latest .

# Run
docker run -d -p 8000:8000 --name agent-corex agent-corex:latest

# Check logs
docker logs agent-corex

# Stop
docker stop agent-corex
```

### Using Pre-built Image (When Available)
```bash
docker pull ankitpro/agent-corex:latest
docker run -p 8000:8000 ankitpro/agent-corex:latest
```

---

## Configuration

### Default Configuration
Agent-Core works out-of-the-box with sensible defaults:
- MCP config: `config/mcp.json`
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Default method: `hybrid` (keyword + embedding)

### Custom Configuration
```bash
# Use custom MCP config
export MCP_CONFIG=/path/to/custom/mcp.json
agent-corex retrieve "test"

# Or use environment variable
export AGENT_CORE_METHOD=embedding
agent-corex retrieve "test"
```

---

## System Resources

### Disk Space
- **Dependencies**: ~300MB
- **Embedding model**: ~80MB
- **Total**: ~400MB

### Memory Usage
- **Idle**: ~50MB
- **Running query**: ~100MB
- **With embedding model cached**: ~150MB
- **With large tool list (1000s)**: ~200MB

### CPU Usage
- **Keyword ranking**: <1ms (negligible)
- **Embedding search**: 50-100ms (efficient)
- **No GPU required**: CPU only is sufficient

---

## Next Steps

1. ✅ [Verify Installation](#verify-installation)
2. 📖 [Read Quick Start](quickstart.md)
3. 📖 [Read Full Tutorial](tutorial.md)
4. 🚀 [Deploy to Production](deployment.md)

---

## Getting Help

- 📖 [Documentation](https://agent-corex.readthedocs.io)
- 💬 [GitHub Discussions](https://github.com/ankitpro/agent-corex/discussions)
- 🐛 [Issue Tracker](https://github.com/ankitpro/agent-corex/issues)
- 📧 [Email Support](mailto:support@agent-corex.dev)

---

**Installation Status**: ✅ Complete

Proceed to [Quick Start](quickstart.md) to start using Agent-Core!
