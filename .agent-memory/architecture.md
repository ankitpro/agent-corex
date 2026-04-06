# Architecture: agent-corex

> Auto-generated architectural overview. Confidence: 100%. Add corrections in `.agent-memory/overrides/`.

## Major boundaries

- **`apps/`** — production source code
- **`packages/`** — production source code
- **`tests/`** — test suite (separate from production code)
- **`docs/`** — documentation
- **`apps/`** — multiple apps/packages (possible monorepo)
- **`packages/`** — multiple apps/packages (possible monorepo)

## Inferred layout

**Pattern**: Monorepo (multiple apps or packages in one repo)
**FastAPI layout**: expect `main.py` / `app.py`, routers, models, schemas

## Inspect first

- `apps/` — main source code
- `packages/` — main source code
- `pyproject.toml` — project metadata and dependencies
- `README.md` — project intent and setup
- `tests/` — to understand expected behaviour
