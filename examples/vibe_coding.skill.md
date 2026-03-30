---
name: vibe_coding_pack
type: pack
requires:
  - github
  - railway
  - supabase
  - filesystem
  - redis
env:
  GITHUB_TOKEN: required
  SUPABASE_ACCESS_TOKEN: required
  REDIS_URL: optional
test: "List my GitHub repositories and show recent Railway deployments"
ai_instructions: |
  This pack gives you full-stack development superpowers:
  - GitHub: create branches, PRs, review code
  - Railway: deploy services, check logs, manage env vars
  - Supabase: query your database, manage auth, run migrations
  - Filesystem: read/write files in your workspace
  - Redis: cache data, pub/sub messaging
  Start by listing available projects with each tool.
---

# Vibe Coding Pack

Essential tools for fast, full-stack development. Covers the entire deployment
cycle from code to cloud: version control, deployment, databases, file access,
and caching — all accessible via natural language through your AI assistant.

## What's included

| Server     | Purpose                              |
|------------|--------------------------------------|
| github     | PRs, branches, issues, code review   |
| railway    | Deploy services, logs, env vars      |
| supabase   | Postgres, auth, storage, edge fns    |
| filesystem | Read/write files in your workspace   |
| redis      | Caching and pub/sub (optional)       |

## Prerequisites

- A GitHub personal access token (classic or fine-grained)
- A Supabase personal access token (supabase.com → Account → Tokens)
- A Railway account (run `railway login` separately)
- Redis URL if you use Redis (format: `redis://...`)
