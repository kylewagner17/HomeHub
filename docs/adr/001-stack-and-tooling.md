# ADR-001: Stack and M0 tooling

## Status

Accepted (M0 foundation)

## Context

HomeHub is a LAN-hosted family hub with a Python API, PostgreSQL, and React Native mobile client (see [architecture.md](../architecture.md)).

## Decision

| Area | Choice |
|------|--------|
| API framework | FastAPI + Uvicorn |
| Python packaging | `uv` + `pyproject.toml` + `uv.lock` |
| Lint/format | Ruff |
| Server DB | PostgreSQL 16 (Docker) |
| ORM / migrations | SQLAlchemy 2 + Alembic (configured; domain tables in later milestones) |
| DB driver | psycopg 3 (`postgresql+psycopg://`) |
| Mobile | React Native CLI template (TypeScript) |
| Shared contract | `packages/shared` TypeScript types for API errors and health |
| IDs | ULID preferred for sync (implement when first entities land) |
| DI | FastAPI `Depends` only — no DI container |

## Consequences

- CI and developers use `uv sync` / `uv run` in `apps/api`.
- Mobile CI runs lint, Jest, and `tsc` without native builds until a workflow is added.
- Auth libraries (JWT, password hashing) added in M1, not M0.
