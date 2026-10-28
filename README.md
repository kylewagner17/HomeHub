# HomeHub

Centralized household hub (calendar, planning, groceries, maintenance, reminders).  
Architecture and agent rules: [docs/architecture.md](docs/architecture.md), [AGENTS.md](AGENTS.md).

## Prerequisites

- Docker Desktop (API + PostgreSQL)
- Node.js 20+ (mobile tooling)
- Python 3.12+ and [uv](https://docs.astral.sh/uv/) (`python -m uv` works if `uv` is not on PATH)
- Docker Desktop running for `docker compose` (API image build and full stack)

## Quick start (API)

```bash
docker compose up --build
curl http://localhost:8000/health
```

API docs: http://localhost:8000/docs

Auth (M1): `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`  
Families: `POST /api/v1/families`, `POST /api/v1/families/join`, `GET /api/v1/families/{id}`  
Sync (M2): `GET /api/v1/sync/ping`, `POST /api/v1/sync/push`, `GET /api/v1/sync/pull`

After upgrading the API image, migrations run automatically on container start.

## Local API development (without Docker for the app)

```bash
docker compose up -d db
cd apps/api
uv sync --all-extras
uv run pytest
uv run uvicorn homehub.main:app --reload --app-dir src
```

## Mobile

```bash
cd apps/mobile
npm ci
npm run lint
npm test
npm run typecheck
```

Run on device/emulator: see [docs/runbooks/local-dev.md](docs/runbooks/local-dev.md).

## Repository layout

- `apps/api` — Python FastAPI backend
- `apps/mobile` — React Native (TypeScript) client
- `packages/shared` — Shared API contract types
- `docs/` — Architecture, ADRs, runbooks
