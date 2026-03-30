---
name: my-postgres
type: server
env:
  DATABASE_URL: required
connect:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-postgres", "${DATABASE_URL}"]
test: "List all tables in my database"
ai_instructions: |
  You have direct access to a Postgres database.
  Use the query tool to run SELECT statements and inspect the schema.
  For writes, always confirm with the user first.
---

# My Postgres Server

Adds a direct Postgres MCP server using your `DATABASE_URL` connection string.

Supports any Postgres-compatible database: Supabase, Neon, Railway Postgres,
local Docker, Amazon RDS, etc.

## Setup

You will be prompted for `DATABASE_URL` in the format:

    postgresql://user:password@host:5432/dbname
