# HomeHub — Agent Instructions

Primary entry point for coding agents. Read this file before changing code.  
Canonical architecture: [docs/architecture.md](docs/architecture.md).

## Architecture and layer responsibilities

| Layer | Location | Responsibility | Must not |
|-------|----------|----------------|----------|
| **Mobile UI** | `apps/mobile/src/features/*`, shared UI in `apps/mobile/src/components/` | Screens, navigation, role-aware UX, optimistic UI | Enforce authorization alone; embed business rules duplicated from API |
| **Mobile data & sync** | `apps/mobile/src/db/`, `apps/mobile/src/sync/` | Local DB, outbox, sync client, conflict handling per documented policy | Talk to PostgreSQL directly; bypass sync for family-scoped writes |
| **API routes** | `apps/api/src/homehub/modules/<domain>/routes.py` (or `router.py`) | HTTP, auth context, request/response mapping | SQL or business rules inline beyond validation |
| **Application services** | `apps/api/src/homehub/modules/<domain>/service.py` | Use cases, orchestration, tenancy checks | Import another module’s repository directly |
| **Domain** | `apps/api/src/homehub/modules/<domain>/models.py`, `exceptions.py` | Entities, invariants, domain errors | FastAPI or SQLAlchemy imports |
| **Persistence** | `apps/api/src/homehub/modules/<domain>/repository.py`, `packages/db/` or `apps/api/alembic/` | Queries, transactions | Cross-module table access without service API |
| **Jobs** | `apps/api/src/homehub/jobs/` | Reminders, push dispatch, import queues | Long blocking work on request thread |
| **Shared contract** | `packages/shared/`, OpenAPI under `docs/api/` | DTOs, error codes, constants shared with mobile | Domain business logic |
| **Integrations** | `apps/api/src/homehub/modules/integrations/` | OAuth, Google/Outlook import pipelines | Overwrite internal calendar on import |

**Tenancy:** Server is authoritative for auth. Every family-scoped operation filters by `family_id` and membership/role.  
**Offline:** Mobile may cache and queue; server wins on permission conflicts unless an ADR says otherwise for a specific entity.

## Before you change code

1. Inspect existing code in the target module and mirror its patterns.
2. Do not introduce a new pattern (state library, folder layout, error type) without checking the rest of the repo; prefer extending what exists.
3. Scope changes to the task: no drive-by refactors or unrelated formatting.
4. **Comments:** Follow [.cursor/rules/code-comments.mdc](.cursor/rules/code-comments.mdc) — explain complex or non-obvious code; avoid line-by-line narration.

## Where to put new artifacts

| Artifact | Location |
|----------|----------|
| New domain feature (API) | `apps/api/src/homehub/modules/<domain>/` — add `routes`, `service`, `repository`, `schemas` as siblings |
| New domain feature (mobile) | `apps/mobile/src/features/<domain>/` — screens, hooks, module-local components |
| Cross-feature mobile UI | `apps/mobile/src/components/` |
| New migration (server) | Alembic under API app (path fixed when M0 lands); name descriptively |
| New migration (local DB) | `apps/mobile/src/db/migrations/` |
| Background task | `apps/api/src/homehub/jobs/<name>.py`, register in job runner |
| Shared types / API client | `packages/shared/` or generated from OpenAPI |
| Architecture change | `docs/architecture.md` + new ADR in `docs/adr/` |
| Public API change | OpenAPI spec + mobile client types; note in PR/commit summary |
| Runbook (ops) | `docs/runbooks/` |

**Module names** (API and mobile should align): `auth`, `families`, `calendar`, `integrations`, `planning`, `reminders`, `groceries`, `maintenance`, `sync`.

## Task definition of done

- [ ] Behavior matches task; no duplicated business logic between mobile and API (shared rules live on API; mobile only mirrors for offline UX with sync).
- [ ] New behavior has automated tests; bug fixes include a regression test when practical.
- [ ] Lint, typecheck, and relevant tests pass locally (same commands as CI — see below when present).
- [ ] Docker API build succeeds if API touched; mobile bundle/typecheck if mobile touched.
- [ ] Docs updated if architecture, sync protocol, auth, or public API changed.
- [ ] No new dependencies without [docs/standards/dependencies.md](docs/standards/dependencies.md) approval process.
- [ ] No secrets committed; `.env.example` updated if new config keys.
- [ ] New/changed code includes appropriate comments per `code-comments.mdc` (complex areas documented; no comment spam).

## Commands (run from repo root when tooling exists)

| Area | Typical commands |
|------|-------------------|
| API | `cd apps/api && ruff check . && pytest` |
| Mobile | `cd apps/mobile && npm run lint && npm run test && npx tsc --noEmit` |
| Full stack | `docker compose build && docker compose up -d` then hit health endpoint |

If scripts are added under `scripts/` or root `package.json`, prefer those documented in README.

## Cursor rules map

| Rule file | Scope |
|-----------|--------|
| `.cursor/rules/homehub-core.mdc` | Always — workflow, prohibitions, docs, deps |
| `.cursor/rules/code-comments.mdc` | Always — comment quality when implementing code |
| `.cursor/rules/python-api.mdc` | `apps/api/**/*.py` |
| `.cursor/rules/react-native-mobile.mdc` | `apps/mobile/**/*.{ts,tsx}` |
| `.cursor/rules/testing.mdc` | Tests in API and mobile |

## Prohibited without explicit user request

- Microservices, GraphQL, Kubernetes, new databases
- Copy-paste domain logic in mobile that should live in API services
- Guest/anonymous access paths
- Overwriting HomeHub calendar data from external import
- Unrelated refactors, abstraction layers for one call site, or new generic “util” frameworks
