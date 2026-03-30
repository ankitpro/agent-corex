---
name: deploy_pack
type: pack
install: "npm install -g @railway/cli"
requires:
  - railway
  - render
env:
  RENDER_API_KEY: optional
test: "Show my Railway projects and Render services"
ai_instructions: |
  This pack gives you multi-cloud deployment capabilities.
  - Railway: full deploy lifecycle, logs, variables, databases
  - Render: deploy web services, static sites, background workers
  Use `railway login` for Railway auth (no API key needed in env).
  Render requires RENDER_API_KEY from dashboard.render.com → Account → API Keys.
---

# Deploy Pack

Multi-cloud deployment tools for Railway and Render.

Install once, deploy anywhere. Manage your entire deployment infrastructure
from your AI assistant — no browser required.

## Auth

- **Railway**: uses `railway login` (OAuth via browser) — no API key in env
- **Render**: set `RENDER_API_KEY` from your Render dashboard
