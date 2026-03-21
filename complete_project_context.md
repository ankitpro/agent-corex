# Agent-Core: Complete Project Context

## 🧠 Overview

Agent-Core is a lightweight, MCP-native **tool retrieval engine** designed to solve a core problem in LLM systems:

> **How do you efficiently select the top-N relevant tools from hundreds of available MCP tools without bloating context or causing hallucinations?**

---

## 🎯 Core Problem

Modern LLM systems suffer from:

* Context window bloat when too many tools are provided
* Tool selection ambiguity
* Increased hallucination due to irrelevant tools
* Latency and cost overhead

---

## 💡 Solution

Agent-Core introduces:

> **A retrieval-first architecture that dynamically selects the most relevant tools from MCP servers**

---

## 🏗️ High-Level Architecture

```
User / LLM
   ↓
Agent-Core (Retrieval Engine)
   ↓
MCP Manager
   ↓
MCP Clients
   ↓
MCP Servers (Filesystem, Git, etc.)
```

---

## 🔑 Core Principles

* Retrieval over execution
* Minimal context exposure
* MCP-native integration
* Stateless + scalable design
* Separation of concerns

---

# 🧩 Core Components

## 1. Retrieval Engine (Core IP)

Responsible for:

* Scoring tools based on query
* Ranking tools
* Returning top_k tools

### Flow:

```
query → filter → score → rank → top_k
```

---

## 2. MCP Layer

### Components:

* `mcp_client.py` → Handles JSON-RPC communication
* `mcp_loader.py` → Loads MCP servers from config
* `mcp_manager.py` → Aggregates tools across servers

### Responsibilities:

* Start MCP servers
* Fetch tool metadata
* Normalize tool schema

---

## 3. Tool Registry

Stores:

* tool name
* description
* schema
* server

---

## 4. API Layer

Endpoints:

* `/retrieve_tools`
* `/health`

---

# 📦 Open Source (OSS) Scope – V1

## ✅ Included

* MCP client (simplified)
* MCP loader (single config)
* MCP manager (tool aggregation only)
* Retrieval engine (basic ranking)
* FastAPI server
* CLI (minimal)
* Tests
* Example usage

---

## ❌ Excluded (Moved to Enterprise)

* Tool execution (`call_tool`)
* Agent runtime
* Multi-agent orchestration
* Advanced caching
* Observability
* Tool marketplace
* Embedding pipelines (advanced)

---

# 🧠 Retrieval Strategy (V1)

### Basic:

* Keyword overlap scoring

### Future:

* Embedding-based similarity
* Usage-based ranking
* Context-aware ranking

---

# ⚙️ Tech Stack

## Backend

* Python
* FastAPI
* Uvicorn

## MCP Communication

* JSON-RPC over STDIO

## Optional (Later)

* Redis (caching)
* PostgreSQL (analytics)
* Sentence Transformers (embeddings)

---

# ☁️ Hosting Strategy

## Initial

* Single FastAPI server
* Hosted on lightweight infra (Railway / Render)

## Scaling

* Containerized deployment
* Horizontal scaling
* API gateway + rate limiting

---

# 🔐 Authentication

* API key based
* Stored as environment variable

---

# 💰 Monetization Strategy

## Core Idea

> Charge for **intelligent tool retrieval**, not execution

---

## Pricing Model

### 🟢 Free Tier

* 1,000 queries/month
* Basic ranking
* Community MCP tools

---

### 🟡 Starter ($9/month)

* 50,000 queries
* Faster responses

---

### 🔵 Pro ($29/month)

* 200,000 queries
* Improved ranking (semantic)

---

### 🏢 Team ($99+/month)

* Shared usage
* Analytics dashboard

---

## Enterprise (Custom Pricing)

* Private MCP servers
* Custom ranking models
* On-prem deployment
* Security + audit logs

---

# 💵 Cost Structure

## Early Stage

* ~$25–50/month infra

## Scaling

* Linear with API usage
* High margins (no LLM cost)

---

## Break-even

* ~4–5 paid users (at $9/month)

---

# 🔥 Revenue Streams

1. API usage (primary)
2. Advanced ranking (premium)
3. Custom MCP support
4. Analytics dashboard
5. Enterprise licensing

---

# 🧩 Advanced Product Vision

## 1. MCP Marketplace

* Curated list of MCP tools
* Pre-indexed and optimized

---

## 2. Local Agent-Core Client

CLI tool:

```
agent-core init
agent-core install <mcp>
agent-core run
```

Responsibilities:

* Install MCP servers
* Maintain local cache
* Lazy load tools
* Call cloud API for ranking

---

## 3. Embedding Layer

### Marketplace tools:

* Precomputed embeddings (shared)

### Custom tools:

* Computed on demand (paid feature)

---

## 4. Observability

* Tool usage tracking
* Success/failure rates
* Optimization insights

---

# 🧠 Caching Strategy

## Local Cache

* Tool metadata
* Optional embeddings

## Cloud Cache

* Shared embeddings
* Popular queries

---

# 🚀 Product Evolution Roadmap

---

## Phase 1 — OSS Launch

* Core retrieval engine
* MCP integration
* Basic API
* CLI
* Documentation

---

## Phase 2 — Monetization Start

* Hosted API
* API key system
* Rate limiting
* Usage tracking

---

## Phase 3 — Intelligence Layer

* Embedding-based ranking
* Improved scoring
* Feedback loops

---

## Phase 4 — Marketplace

* MCP discovery
* Tool curation
* Precomputed embeddings

---

## Phase 5 — Enterprise

* Private deployments
* Custom ranking
* Advanced analytics

---

# ⚠️ Risks

* Overengineering early
* Losing focus on retrieval
* Competing with agent frameworks
* Poor UX for integration

---

# 🧠 Key Differentiator

> **We don’t build agents. We make agents work better.**

---

# 🔥 Positioning

Agent-Core is:

* NOT a framework
* NOT an agent system

It is:

> **“The intelligence layer for MCP tool selection”**

---

# 📊 Success Metrics

* Reduction in tool count per query
* Improvement in tool selection accuracy
* Latency reduction
* Token savings

---

# 🔮 Future Possibilities

* Learning-based ranking
* Cross-user optimization
* MCP ecosystem standardization
* Tool recommendation engine

---

# 💥 Final Vision

Agent-Core becomes:

> **The default retrieval layer for MCP-based LLM systems**

---

# 🧾 Summary

* OSS → adoption
* API → monetization
* Intelligence → moat
* Marketplace → ecosystem
* Enterprise → scale

---
