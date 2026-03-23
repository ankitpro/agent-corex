---
layout: page
title: Agent-Corex - Intelligent Tool Selection for LLMs
description: Fast, accurate MCP tool retrieval engine with hybrid semantic + keyword ranking
permalink: /
---

# Agent-Corex

**Intelligent Tool Selection for LLM-Based Systems**

> Stop feeding your LLM tools it doesn't need. Agent-Corex intelligently selects the top N most relevant tools in milliseconds using hybrid semantic + keyword ranking.

---

## Install

### Homebrew (macOS / Linux — no Python required)
```bash
brew tap ankitpro/agent-corex
brew install agent-corex
```

### Direct binary (no Python required)

| Platform | Command |
|----------|---------|
| **macOS** arm64 (M1/M2/M3 + Intel via Rosetta) | `curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-macos-arm64 -o /usr/local/bin/agent-corex && chmod +x /usr/local/bin/agent-corex` |
| **Linux** x86_64 | `curl -fsSL https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-linux-x86_64 -o /usr/local/bin/agent-corex && chmod +x /usr/local/bin/agent-corex` |
| **Windows** x86_64 | [Download .exe](https://github.com/ankitpro/agent-corex/releases/latest/download/agent-corex-windows-x86_64.exe) |

### pip (Python 3.8+)
```bash
pip install agent-corex
```

**[Full installation guide →](/installation)**

---

## The Problem We Solve

When building LLM agents with access to hundreds of tools, including all of them in the system prompt causes:

- **Context Bloat** — 30K+ tokens per request
- **Higher Costs** — 68% more expensive per query
- **Slower Inference** — 4–5x latency increase
- **Model Confusion** — LLM picks random tools when overwhelmed

Agent-Corex solves this by intelligently selecting only the 5–10 tools your LLM actually needs.

---

## Quick Stats

| Metric | Impact |
|--------|--------|
| **Token Reduction** | 50–75% fewer tokens |
| **Speed Improvement** | 3–5x faster inference |
| **Cost Savings** | 68% reduction per query |
| **Selection Accuracy** | 92% precision (top-5) |

---

## One-Command Setup

Connect Agent-CoreX to Claude Desktop, Cursor, VS Code, or VS Code Insiders:

```bash
agent-corex login --key acx_your_key
agent-corex init
```

Agent-CoreX detects your installed tools, backs up their configs, and **safely merges** the gateway entry — existing MCP servers are never touched.

**[Full setup guide →](/mcp-setup)**

---

## Key Features

### Three Ranking Methods

| Method | Speed | Best For |
|--------|-------|----------|
| **Keyword** | <1ms | Instant filtering |
| **Hybrid** | 50–100ms | **Recommended** |
| **Embedding** | 50–100ms | Maximum semantic accuracy |

### MCP Marketplace

```bash
agent-corex registry              # browse catalog
agent-corex install-mcp github    # install GitHub MCP server
agent-corex list                  # see installed servers
agent-corex update                # update all server configs
```

### Multiple Interfaces

```
Python SDK  →  REST API  →  CLI Tool  →  MCP Gateway
```

---

## Documentation

- **[⚡ Quick Start](/quickstart)** — 5-minute setup
- **[📦 Installation](/installation)** — all install methods (Homebrew, binary, pip, source)
- **[🔌 MCP Setup Guide](/mcp-setup)** — connect Claude Desktop, Cursor, VS Code
- **[🔌 API Reference](/api)** — Python SDK, REST API, CLI reference
- **[🚀 Deployment](/deployment)** — production deployment

---

## Community & Support

- [GitHub Issues](https://github.com/ankitpro/agent-corex/issues) — bugs and feature requests
- [GitHub Discussions](https://github.com/ankitpro/agent-corex/discussions) — questions and discussion
- [PyPI](https://pypi.org/project/agent-corex/) — Python package
- [Releases](https://github.com/ankitpro/agent-corex/releases) — binary downloads and changelogs

---

## License

Agent-Corex is released under the **MIT License**.
**Author**: [Ankit Agarwal](https://www.linkedin.com/in/ankitagarwal94)
