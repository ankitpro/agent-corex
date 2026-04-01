---
layout: page
title: Installation Guide
description: Complete setup instructions for Agent-Corex
permalink: /installation/
---

# Installation Guide

Three ways to install Agent-Corex — pick what works best for you.

---

## Method 1: Homebrew (macOS / Linux) — Recommended

No Python required. Installs a self-contained binary.

```bash
brew tap ankitpro/agent-corex
brew install agent-corex
```

Verify:
```bash
agent-corex --version
```

To upgrade later:
```bash
brew update && brew upgrade agent-corex
```

---

## Method 2: Direct Binary Download — No Python Required

Downloads a single standalone executable. No dependencies, no Python needed.

### macOS (arm64 — M1/M2/M3 and Intel via Rosetta 2)

```bash
curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-macos-arm64 \
  -o /usr/local/bin/agent-corex
chmod +x /usr/local/bin/agent-corex
agent-corex --version
```

### Linux (x86_64)

```bash
curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-linux-x86_64 \
  -o /usr/local/bin/agent-corex
chmod +x /usr/local/bin/agent-corex
agent-corex --version
```

### Windows (x86_64)

#### System-wide install (recommended — run PowerShell as Administrator)

Right-click PowerShell → **Run as administrator**, then:

```powershell
# Download and install to System32 so 'agent-corex' works from anywhere
Invoke-WebRequest `
  -Uri https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-windows-x86_64.exe `
  -OutFile "$env:SystemRoot\System32\agent-corex.exe"

# Verify
agent-corex --version
```

#### Per-user install (no admin required)

```powershell
# Create a local bin folder and add it to your user PATH
$bin = "$env:USERPROFILE\bin"
New-Item -ItemType Directory -Force -Path $bin | Out-Null

Invoke-WebRequest `
  -Uri https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-windows-x86_64.exe `
  -OutFile "$bin\agent-corex.exe"

# Add to PATH permanently for current user (takes effect in new terminals)
$current = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($current -notlike "*$bin*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$current;$bin", "User")
}

# Use immediately in this session
$env:Path += ";$bin"
agent-corex --version
```

#### Direct download

[Download agent-corex-windows-x86_64.exe](https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-windows-x86_64.exe)

> **Note:** Always run from a terminal (Command Prompt or PowerShell), not by double-clicking.
> Double-clicking a CLI tool closes the window instantly before you can read any output.

### Verify SHA256 checksum (optional)

```bash
# macOS
curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-macos-arm64.sha256
shasum -a 256 /usr/local/bin/agent-corex

# Linux
curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-linux-x86_64.sha256
sha256sum /usr/local/bin/agent-corex
```

---

## Method 3: pip (Python 3.8+)

Best for developers who already have Python.

```bash
pip install agent-corex
```

Verify:
```bash
agent-corex --version
```

### Virtual environment (recommended for pip)

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install agent-corex
agent-corex --version
```

### Upgrade

```bash
pip install --upgrade agent-corex
```

---

## Method 4: uvx — No Install Required

If you have [uv](https://docs.astral.sh/uv/) installed, you can run agent-corex as an ephemeral tool without a global install.

**Install uv first (if you haven't):**
```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Run any agent-corex command directly:**
```bash
uvx agent-corex --version
uvx agent-corex login
uvx agent-corex init
uvx agent-corex serve       # starts the MCP gateway
```

**Pin to a specific version:**
```bash
uvx agent-corex@1.8.0 serve
```

uvx fetches the package from PyPI, caches it locally, and runs it in an isolated environment. No virtual environment or PATH changes needed.

> **When to use uvx:** ideal for CI pipelines, one-off commands, or when you want to keep your global Python environment clean. For day-to-day CLI use, Homebrew or direct binary is faster (no startup overhead).

---

## Method 5: From Source

For development or cutting-edge builds.

```bash
git clone https://github.com/ankitpro/agent-corex.git
cd agent-corex
pip install -e ".[dev]"
agent-corex --version
```

---

## After Installing — Connect to Your AI Tools

Wire Agent-CoreX into Claude Desktop, Cursor, VS Code, or VS Code Insiders with one command:

```bash
agent-corex login --key acx_your_key   # authenticate first
agent-corex detect                      # see which tools are installed
agent-corex init                        # inject into all detected tools
agent-corex status                      # verify injection
```

### Using uvx instead of a global install

If you installed via **Method 4 (uvx)** and want your AI tools to use uvx to launch the MCP gateway, add the following to your tool's config manually (or run `agent-corex init` — it auto-detects if `agent-corex` is on PATH, otherwise you'll need the manual snippet):

**Claude Desktop / Cursor** (`claude_desktop_config.json` / `mcp.json`):
```json
{
  "mcpServers": {
    "agent-corex": {
      "command": "uvx",
      "args": ["agent-corex", "serve"]
    }
  }
}
```

**VS Code** (`settings.json`):
```json
{
  "mcp": {
    "servers": {
      "agent-corex": {
        "type": "stdio",
        "command": "uvx",
        "args": ["agent-corex", "serve"]
      }
    }
  }
}
```

See [MCP Setup Guide](/mcp-setup) for full config file paths per OS.

### Config file locations

| Tool | Platform | Path |
|------|----------|------|
| Claude Desktop | Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Claude Desktop | macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Claude Desktop | Linux | `~/.config/Claude/claude_desktop_config.json` |
| Cursor | Windows | `%APPDATA%\Cursor\User\mcp.json` |
| Cursor | macOS | `~/Library/Application Support/Cursor/User/mcp.json` |
| Cursor | Linux | `~/.config/Cursor/User/mcp.json` |
| VS Code | Windows | `%APPDATA%\Code\User\mcp.json` |
| VS Code | macOS | `~/Library/Application Support/Code/User/mcp.json` |
| VS Code | Linux | `~/.config/Code/User/mcp.json` |

---

## Troubleshooting

### "agent-corex: command not found" (pip install)
```bash
# Ensure pip scripts directory is in PATH, or use:
python -m agent_core.cli.main version
```

### "Permission denied" on macOS/Linux binary
```bash
chmod +x /usr/local/bin/agent-corex
```

### macOS Gatekeeper warning on binary
```bash
xattr -d com.apple.quarantine /usr/local/bin/agent-corex
```

### Windows Defender warning on .exe
The binary is unsigned. Allow it in Windows Security → Virus & Threat Protection → Allow an app.

---

## Getting Help

- [GitHub Issues](https://github.com/ankitpro/agent-corex/issues)
- [GitHub Discussions](https://github.com/ankitpro/agent-corex/discussions)
- Run `agent-corex doctor` for a built-in health check
