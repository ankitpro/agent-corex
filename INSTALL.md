# Installation Guide

Agent-Core can be installed using multiple methods. Choose the one that best fits your workflow.

## Quick Install (Recommended)

### macOS / Linux with curl

```bash
curl -fsSL https://raw.githubusercontent.com/your-org/agent-core/main/install-curl.sh | bash
```

### Windows

```powershell
# Via PowerShell
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/your-org/agent-core/main/install.bat'))

# Or download and run
curl https://raw.githubusercontent.com/your-org/agent-core/main/install.bat -o install.bat
.\install.bat
```

---

## pip (PyPI)

The easiest way to install Agent-Core is via pip:

### Basic Installation

```bash
pip install agent-core
```

### With Optional Dependencies

```bash
# For Redis caching support
pip install agent-core[redis]

# For development tools (testing, formatting, linting)
pip install agent-core[dev]

# With everything
pip install agent-core[dev,redis]
```

### Upgrade

```bash
pip install --upgrade agent-core
```

### Uninstall

```bash
pip uninstall agent-core
```

---

## Source Installation

### From GitHub

```bash
git clone https://github.com/your-org/agent-core.git
cd agent-core
pip install -e .
```

### From Tarball

```bash
curl -L https://github.com/your-org/agent-core/archive/refs/tags/v1.0.0.tar.gz -o agent-core.tar.gz
tar xzf agent-core.tar.gz
cd agent-core-1.0.0
pip install -e .
```

---

## Platform-Specific Instructions

### macOS

```bash
# Using Homebrew (if we add brew support)
brew install agent-core

# Or via pip
python3 -m pip install agent-core
```

### Ubuntu / Debian

```bash
sudo apt-get install python3-pip python3-venv

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install Agent-Core
pip install agent-core
```

### Windows

```cmd
# Install Python 3.8+ from python.org

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install Agent-Core
pip install agent-core
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install agent-core

EXPOSE 8000

CMD ["agent-core", "start", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t agent-core .
docker run -p 8000:8000 agent-core
```

---

## Verification

After installation, verify it works:

```bash
# Check version
agent-core version

# Check configuration
agent-core config

# Check API health (if running)
agent-core health
```

---

## Getting Started

### 1. Start the API Server

```bash
agent-core start
```

Server runs at `http://127.0.0.1:8000`

### 2. Retrieve Tools (in another terminal)

```bash
agent-core retrieve "edit a file" --top-k 5
```

### 3. Visit Interactive API Docs

Open browser to: `http://localhost:8000/docs`

---

## Virtual Environments (Recommended)

Using virtual environments is strongly recommended to isolate dependencies:

### Create Virtual Environment

```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Install in Virtual Environment

```bash
pip install agent-core
```

### Deactivate When Done

```bash
deactivate
```

---

## Troubleshooting

### Python Not Found

```
Error: python3: command not found
```

**Solution:** Install Python 3.8+ from https://www.python.org/downloads/

### pip Not Found

```
Error: pip: command not found
```

**Solution:**
```bash
python -m pip install agent-core
```

### Permission Denied

```
Error: [Errno 13] Permission denied
```

**Solution 1:** Use virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate
pip install agent-core
```

**Solution 2:** Install for user only
```bash
pip install --user agent-core
```

### Sentence Transformers Model Download Fails

```
Error: Failed to download model
```

**Solution:** The model is automatically downloaded on first use (30-60 seconds). Ensure you have internet connectivity and ~200MB free disk space.

Manual download:
```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Port Already in Use

```
Error: Address already in use
```

**Solution:** Use a different port
```bash
agent-core start --port 8001
```

### Module Not Found After Install

```
ModuleNotFoundError: No module named 'agent_core'
```

**Solution:** Verify installation
```bash
pip show agent-core
python -c "import agent_core; print(agent_core.__version__)"
```

If not found, reinstall:
```bash
pip uninstall agent-core
pip install agent-core
```

---

## System Requirements

- **Python:** 3.8 or higher
- **RAM:** 512 MB minimum (with embedding model: 150 MB)
- **Disk:** 500 MB minimum (for model caching)
- **OS:** Windows, macOS, Linux

### Optional

- **Redis:** For caching support (install with `agent-core[redis]`)
- **Node.js:** For MCP servers that use npm (e.g., filesystem, memory)

---

## Development Installation

For contributing to Agent-Core:

```bash
git clone https://github.com/your-org/agent-core.git
cd agent-core

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Format code
black agent_core tests

# Type check
mypy agent_core
```

---

## Docker Installation

### Using Official Image

```bash
docker pull agent-core:latest
docker run -p 8000:8000 agent-core:latest
```

### Building Locally

```bash
git clone https://github.com/your-org/agent-core.git
cd agent-core
docker build -t agent-core:latest .
docker run -p 8000:8000 agent-core:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  agent-core:
    image: agent-core:latest
    ports:
      - "8000:8000"
    environment:
      - AGENT_CORE_CONFIG=/app/config/mcp.json
    volumes:
      - ./config:/app/config
```

Run with:
```bash
docker-compose up
```

---

## Next Steps

- [Read the Documentation](README.md)
- [View Examples](examples/)
- [Contribute](CONTRIBUTING.md)
- [View Issues](https://github.com/your-org/agent-core/issues)

---

## Getting Help

- 📖 [Documentation](README.md)
- 🐛 [Report Issues](https://github.com/your-org/agent-core/issues)
- 💬 [Discussions](https://github.com/your-org/agent-core/discussions)
- 📧 Email: hello@agent-core.ai
