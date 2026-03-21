# Installation Guide

Agent-Core can be installed using multiple methods. Choose the one that best fits your workflow.

## Quick Install (Recommended)

### macOS / Linux with curl

```bash
curl -fsSL https://raw.githubusercontent.com/your-org/agent-corex/main/install-curl.sh | bash
```

### Windows

```powershell
# Via PowerShell
iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/your-org/agent-corex/main/install.bat'))

# Or download and run
curl https://raw.githubusercontent.com/your-org/agent-corex/main/install.bat -o install.bat
.\install.bat
```

---

## pip (PyPI)

The easiest way to install Agent-Core is via pip:

### Basic Installation

```bash
pip install agent-corex
```

### With Optional Dependencies

```bash
# For Redis caching support
pip install agent-corex[redis]

# For development tools (testing, formatting, linting)
pip install agent-corex[dev]

# With everything
pip install agent-corex[dev,redis]
```

### Upgrade

```bash
pip install --upgrade agent-corex
```

### Uninstall

```bash
pip uninstall agent-corex
```

---

## Source Installation

### From GitHub

```bash
git clone https://github.com/your-org/agent-corex.git
cd agent-corex
pip install -e .
```

### From Tarball

```bash
curl -L https://github.com/your-org/agent-corex/archive/refs/tags/v1.0.0.tar.gz -o agent-corex.tar.gz
tar xzf agent-corex.tar.gz
cd agent-corex-1.0.0
pip install -e .
```

---

## Platform-Specific Instructions

### macOS

```bash
# Using Homebrew (if we add brew support)
brew install agent-corex

# Or via pip
python3 -m pip install agent-corex
```

### Ubuntu / Debian

```bash
sudo apt-get install python3-pip python3-venv

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install Agent-Core
pip install agent-corex
```

### Windows

```cmd
# Install Python 3.8+ from python.org

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install Agent-Core
pip install agent-corex
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install agent-corex

EXPOSE 8000

CMD ["agent-corex", "start", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t agent-corex .
docker run -p 8000:8000 agent-corex
```

---

## Verification

After installation, verify it works:

```bash
# Check version
agent-corex version

# Check configuration
agent-corex config

# Check API health (if running)
agent-corex health
```

---

## Getting Started

### 1. Start the API Server

```bash
agent-corex start
```

Server runs at `http://127.0.0.1:8000`

### 2. Retrieve Tools (in another terminal)

```bash
agent-corex retrieve "edit a file" --top-k 5
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
pip install agent-corex
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
python -m pip install agent-corex
```

### Permission Denied

```
Error: [Errno 13] Permission denied
```

**Solution 1:** Use virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate
pip install agent-corex
```

**Solution 2:** Install for user only
```bash
pip install --user agent-corex
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
agent-corex start --port 8001
```

### Module Not Found After Install

```
ModuleNotFoundError: No module named 'agent_core'
```

**Solution:** Verify installation
```bash
pip show agent-corex
python -c "import agent_core; print(agent_core.__version__)"
```

If not found, reinstall:
```bash
pip uninstall agent-corex
pip install agent-corex
```

---

## System Requirements

- **Python:** 3.8 or higher
- **RAM:** 512 MB minimum (with embedding model: 150 MB)
- **Disk:** 500 MB minimum (for model caching)
- **OS:** Windows, macOS, Linux

### Optional

- **Redis:** For caching support (install with `agent-corex[redis]`)
- **Node.js:** For MCP servers that use npm (e.g., filesystem, memory)

---

## Development Installation

For contributing to Agent-Core:

```bash
git clone https://github.com/your-org/agent-corex.git
cd agent-corex

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
docker pull agent-corex:latest
docker run -p 8000:8000 agent-corex:latest
```

### Building Locally

```bash
git clone https://github.com/your-org/agent-corex.git
cd agent-corex
docker build -t agent-corex:latest .
docker run -p 8000:8000 agent-corex:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  agent-corex:
    image: agent-corex:latest
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
- [View Issues](https://github.com/your-org/agent-corex/issues)

---

## Getting Help

- 📖 [Documentation](README.md)
- 🐛 [Report Issues](https://github.com/your-org/agent-corex/issues)
- 💬 [Discussions](https://github.com/your-org/agent-corex/discussions)
- 📧 Email: hello@agent-corex.ai
