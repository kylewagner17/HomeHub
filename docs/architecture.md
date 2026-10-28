# HomeHub — Architecture & Requirements

Living document for project discovery, architecture, standards, and milestones.  
**Status:** Approved baseline. Agent instructions: [AGENTS.md](../AGENTS.md), `.cursor/rules/`. Implementation begins after explicit go-ahead.

---

## 1. Vision and scope

### 1.1 Purpose

HomeHub is a centralized household hub for calendar, planning, maintenance, reminders, grocery lists, and related family operations. Data is organized per **family** (internal name: **node**): multiple users belong to one family; families do not share data with each other.

### 1.2 In scope (current)

| Area | Direction |
|------|-----------|
| **Calendar** | Internal calendar; optional one-way import from Google/Outlook when the user triggers sync (no overwrite; add only events not already present) |
| **Planning** | Tasks, boards, and broader planning — phased; target includes “all of the above” over time |
| **Reminders** | Due dates, recurrence; in-app and push notifications |
| **Groceries** | Multiple lists, staples, real-time sharing; store-aware pricing and estimated totals |
| **Maintenance** | Assets and recurring jobs (e.g. filters, oil changes) with **timers / intervals** until next due |
| **Access** | Individual login; personal + family-visible data; role-based views |
| **Mobile** | **Mobile-first** React Native app (sideloaded); **local database** on device for offline use |
| **Backend** | Hosted on developer PC (Docker), later mini PC; **LAN-only** for now |
| **History** | Retain all history (no automatic purge) |

### 1.3 Out of scope (for now)

- AI assistants, voice, smart-home bridges (may be added later)
- Guest / read-only role
- Multi-home / cross-family sharing (may be added later; model should not block it)
- Public internet exposure (LAN-only deployment initially)

### 1.4 Future considerations (design without building)

- Multiple homes per account or org hierarchy above “family”
- External integrations beyond calendar import
- Optional web admin or companion UI (stack allows it; not primary client v1)

---

## 2. Users, families, and authorization

### 2.1 Concepts

| Concept | Description |
|---------|-------------|
| **User** | Individual account with login credentials |
| **Family (node)** | Tenant boundary: all plans, lists, maintenance, and shared calendar context for one household |
| **Membership** | User belongs to one or more families (exact cardinality TBD in Phase 2; immediate goal is **one family per user** with model ready for more) |
| **Event / resource ownership** | User owns created items; ownership determines default edit rights |
| **Family visibility** | Family members can **view** or **view + edit** per resource or policy (see below) |

### 2.2 Login and visibility model

- Users **log in individually** (no shared family password).
- After login, the app shows:
  - **Personal** calendar events and items scoped to the user
  - **Family** events and shared data for the family(ies) they belong to
- **Ownership:** The creating user owns the record unless explicitly transferred (rules TBD in API design).
- **Family access:** Configurable per event or via role defaults — family can view or edit when allowed by owner or family policy.
- **No guest role.**

### 2.3 Roles (role-based dashboard)

- Dashboard and modules respect **roles** within a family (e.g. parent vs child — exact role names and permissions defined in Phase 2).
- Children may see subsets (e.g. chores, assigned tasks) while parents see full family operational view.
- Authorization checks run **on the server**; local DB on mobile enforces UX offline but must reconcile with server rules on sync.

### 2.4 Deployment access

- **LAN-only:** API and sync reachable only on local network (no public URL in v1).
- Mobile devices on the same Wi‑Fi (or VPN extension later) talk to the Docker-hosted backend on the PC / future mini PC.

---

## 3. Platform and client architecture

### 3.1 Primary client: React Native (TypeScript)

- **Distribution:** Sideloaded builds (iOS/Android as applicable); no store requirement for v1.
- **Offline-first:** Local database on device; read/write offline where possible; **sync** with server when online.
- **Notifications:** In-app and **push** (platform-specific setup documented in runbooks).

### 3.2 Backend: Python

- REST (or similar) API consumed by the mobile app.
- Runs in **Docker** on home hardware (PostgreSQL in same compose stack).
- Background jobs: reminder firing, optional calendar sync queues, push dispatch.

### 3.3 Database: PostgreSQL

- System of record on the server.
- Mobile local store (SQLite or equivalent — chosen in implementation) holds a **replica/subset** with sync metadata (versions, tombstones, conflict policy).

### 3.4 Stack summary

| Layer | Technology |
|-------|------------|
| Mobile app | TypeScript, React Native |
| Backend | Python |
| Server DB | PostgreSQL |
| Repo layout | Monorepo |
| Hosting | Docker on local hardware (LAN) |

**Note:** Phase 1 listed Next.js as an optional web stack; **current decision is Python backend + React Native client**, not Next.js as the primary application server. A small internal web tool may be added later without changing this baseline.

### 3.5 High-level diagram

```
┌─────────────────────────────────────────────────────────────┐
│  React Native app (TypeScript)                              │
│  - UI, roles, offline local DB                              │
│  - Push + in-app notifications                              │
│  - Calendar sync trigger → API                              │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS (LAN)
┌──────────────────────────▼──────────────────────────────────┐
│  Python API (Docker)                                          │
│  - Auth, families, RBAC, domain modules                     │
│  - Sync endpoints, conflict resolution                      │
│  - Import: Google / Outlook (on user action)                │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  PostgreSQL          Job worker         Push provider
  (system of          (reminders,        (FCM/APNs via
   record)             maintenance)       configured keys)
```

### 3.6 Sync and offline (principles)

- **Server authoritative** for permissions and merge outcomes unless explicitly defined otherwise (e.g. last-write-wins for grocery check-off — to be specified per entity in Phase 2).
- Local DB enables groceries, lists, calendar viewing, and queued writes offline.
- Real-time grocery sharing targets **online sync** (WebSocket or polling — decision in implementation); offline queues flush when connected.

---

## 4. Domain modules

### 4.1 Calendar

- Internal events (create/edit/delete on HomeHub).
- **External sync (user-initiated):** Connect Google and/or Outlook; **import only**:
  - Do **not** overwrite existing HomeHub events from external sources.
  - Add external events that are **not already** on the calendar (dedupe strategy: time range + title/external id — detailed in implementation).
- Import/export (e.g. iCal) supported per product requirement.
- Personal vs family visibility and edit rules apply per event.

### 4.2 Planning

- Phased delivery; end state includes task lists, Kanban/board-style planning, and broader planning surfaces.
- Integrate with dashboard and calendar (due dates, milestones) as features land.

### 4.3 Reminders

- One-off and recurring reminders tied to users/family context as appropriate.
- Scheduler on backend; delivery via in-app and push.

### 4.4 Groceries

- **Multiple lists** per family.
- **Staples** (reusable items / templates).
- **Real-time sharing** among family members when online.
- **Store-aware pricing:** lookup or stored prices per store; **estimated cart total** for chosen store (integration source for prices TBD — manual entry vs external API — Phase 2).

### 4.5 Planned maintenance

- Assets (HVAC, vehicles, appliances, etc.).
- Maintenance tasks with **interval timers** (e.g. “replace filter every N days/months/miles” — unit rules in implementation).
- Next-due computation, history log, dashboard surfacing of overdue/upcoming.

### 4.6 Hub / dashboard

- **Role-based** landing: widgets/summaries per module (calendar, reminders, maintenance, groceries, planning).
- Deep links into module screens from mobile app.

---

## 5. System architecture (backend)

### 5.1 Style: modular monolith (Python)

Single deployable API with clear module boundaries:

| Module | Responsibility |
|--------|----------------|
| `auth` | Login, sessions/tokens, device registration for push |
| `families` | Nodes, membership, roles |
| `calendar` | Events, visibility, dedupe, export/import |
| `integrations` | OAuth for Google/Outlook, import pipelines |
| `planning` | Tasks, boards (phased) |
| `reminders` | CRUD, recurrence, notification scheduling |
| `groceries` | Lists, items, staples, pricing, realtime channel |
| `maintenance` | Assets, schedules, completion history |
| `sync` | Mobile sync protocol, change feeds, idempotency |

**Communication:** In-process calls between modules; shared kernel for IDs, timestamps (UTC), tenancy (`family_id`), and error types. No microservices in v1.

### 5.2 Cross-cutting

- **Tenancy:** Every family-scoped row keyed by `family_id`; queries always filter by membership.
- **Time:** Store UTC; display using user/family timezone settings.
- **Audit:** `created_at`, `updated_at`, `created_by`; retain history per retention policy (keep all).
- **Logging:** Structured logs; no secrets; correlation id per request.

---

## 6. Repository structure (monorepo)

```
HomeHub/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml          # api, postgres, worker (optional separate service)
├── docs/
│   ├── architecture.md         # this file
│   ├── adr/                    # architecture decision records
│   └── runbooks/               # backup, restore, LAN setup, sideload builds
├── apps/
│   ├── mobile/                 # React Native (TypeScript)
│   │   └── src/
│   │       ├── features/       # calendar, groceries, maintenance, ...
│   │       ├── sync/
│   │       ├── db/             # local schema, migrations
│   │       └── navigation/
│   └── api/                    # Python backend
│       └── src/
│           └── homehub/
│               ├── main.py
│               ├── modules/    # auth, families, calendar, ...
│               └── jobs/
├── packages/
│   └── shared/                 # Optional: OpenAPI-generated types, shared constants
│       └── (generated or hand-maintained contract)
├── scripts/                    # dev, seed, backup
└── .github/
    └── workflows/              # lint, test, build (mobile + api)
```

**Rationale:** `apps/mobile` and `apps/api` deploy independently but share contracts via OpenAPI or shared package. Domain folders mirror each other conceptually for maintainability.

---

## 7. Coding and testing standards

### 7.1 Conventions

| Area | Standard |
|------|----------|
| **Python** | 3.12+ (pin in Docker); formatter/linter (Ruff or Black + isort — pick one in Phase 2); type hints on public APIs |
| **TypeScript** | `strict: true`; ESLint + Prettier |
| **Naming** | DB: `snake_case`; Python: PEP 8; TS: `camelCase` / `PascalCase` for types |
| **IDs** | UUID or ULID (decide in Phase 2; prefer sortable for sync cursors) |
| **API errors** | Consistent JSON: `{ "error": { "code", "message", "details"? } }` |
| **Validation** | Request validation at API boundary (Pydantic); client validation for UX only |
| **Secrets** | Environment variables; never commit `.env` |

### 7.2 Error handling

- **API:** Map domain exceptions to HTTP status; log stack traces server-side only.
- **Mobile:** User-safe messages; retry/backoff for sync; persist failed mutations in outbox.
- **Integrations:** OAuth token refresh failures surfaced to user; no silent data loss on import.

### 7.3 Testing

| Level | Backend (Python) | Mobile (RN) |
|-------|------------------|-------------|
| Unit | Domain rules (recurrence, next-due maintenance, dedupe) | Reducers, sync helpers, date logic |
| Integration | API + PostgreSQL (containers) | Local DB + sync client against mock API |
| E2E | Critical flows via HTTP | Detox or Maestro (choose in Phase 2) |

**CI gates:** Lint, typecheck, unit + integration tests, Docker build; mobile build on main/tags as resources allow.

### 7.4 Dependency policy

- Prefer standard library and well-maintained packages (PyPI, npm).
- New dependencies require brief justification (security, size, maintenance).
- Lockfiles committed (`poetry.lock` / `uv.lock` / `package-lock.json` — tool choice in Phase 2).

---

## 8. Security, performance, maintainability

### 8.1 Security (LAN-focused)

- Authenticate every API call; enforce **family_id + role** on every mutation and query.
- Hash passwords with modern algorithms (argon2/bcrypt); no custom crypto.
- OAuth tokens for Google/Outlook stored encrypted at rest; minimal scopes.
- TLS on LAN optional but recommended (local CA or reverse proxy) — document in runbook.
- Rate limiting low priority on LAN; still validate input size and prevent abuse from compromised devices on network.

### 8.2 Performance

- Household-scale data volumes; optimize dashboard aggregates with indexed queries.
- Mobile: paginate lists; lazy load calendar ranges.
- Real-time groceries: efficient diffs, not full list replay each change.

### 8.3 Maintainability

- ADRs for sync strategy, auth token model, and calendar dedupe.
- OpenAPI spec as contract between `apps/api` and `apps/mobile`.
- Module boundaries: no cross-module SQL from wrong package; use service interfaces.

---

## 9. Dependencies (initial recommendations)

| Purpose | Recommendation | Notes |
|---------|----------------|-------|
| Python API | FastAPI | Async, Pydantic, OpenAPI |
| ORM / migrations | SQLAlchemy 2 + Alembic | PostgreSQL-native |
| Auth | JWT or session + refresh; device tokens | Align with mobile |
| Jobs | APScheduler or Celery + Redis | Redis only if worker queue needed |
| RN navigation | React Navigation | De facto standard |
| Local DB | WatermelonDB or op-sqlite + Drizzle | Evaluate in Phase 2 for sync fit |
| Push | FCM + APNs | Required keys in `.env.example` |
| Calendar OAuth | Google Calendar API, Microsoft Graph | User-triggered import only |

Defer: Kubernetes, GraphQL, microservices, Redis until worker/realtime needs justify it.

---

## 10. Implementation milestones and acceptance criteria

Order emphasizes **foundation → auth/family → vertical slices**; mobile and sync are first-class from Milestone 1 onward.

### M0 — Foundation

- Monorepo, Docker Compose (API + PostgreSQL), health check, CI skeleton, `.env.example`, this doc + ADR-001 (stack).

**Acceptance:** `docker compose up` on LAN; API health returns OK; CI green on tests.

**Status:** Implemented (see repo root `README.md`).

### M1 — Auth, family (node), roles shell

- User registration/login, create/join family, role assignment, mobile login + secure token storage.

**Acceptance:** Two users in one family; role difference visible on dashboard shell; unauthorized cross-family access denied.

**Status:** Implemented. Roles: see [ADR-002](adr/002-family-roles.md). API: `/api/v1/auth/*`, `/api/v1/families/*`.

### M2 — Mobile offline shell + sync protocol (minimal)

- Local DB, outbox, sync ping; one entity type (e.g. grocery list) end-to-end.

**Acceptance:** Airplane mode edit → reconnect → server reflects change; conflict policy documented.

**Status:** Implemented. See [ADR-003](adr/003-sync-and-local-db.md). API: `/api/v1/sync/*`, minimal grocery lists.

### M3 — Groceries

- Multiple lists, staples, real-time updates online, store + line items + total estimate (manual prices minimum).

**Acceptance:** Family member sees partner’s changes in near real time; totals update for selected store.

**Status:** Implemented. See [ADR-004](adr/004-grocery-realtime-m3.md). Manual store prices; quantity merge and steppers on list detail; 5s pull sync when online.

### M4 — Reminders + push

- CRUD, recurrence, backend scheduler, in-app + push delivery.

**Acceptance:** Reminder fires on device; history retained.

### M5 — Maintenance

- Assets, interval-based next due, complete → reschedule, history.

**Acceptance:** Filter/oil-style interval produces correct next due date after completion.

### M6 — Calendar + import

- Internal events, personal/family visibility, user-triggered Google/Outlook import (non-destructive, dedupe), import/export.

**Acceptance:** Import adds only new events; existing events unchanged; iCal export/import path documented.

### M7 — Planning (phased)

- Wave 1: tasks/checklists; Wave 2: boards; Wave 3: extended planning — each wave has dashboard + role visibility.

**Acceptance:** Per wave checklist in Phase 2 project instructions.

### M8 — Hardening

- Backup/restore runbook tested; push failure handling; sync stress on slow LAN.

**Acceptance:** Restore drill succeeds; no data loss on retained history policy.

---

## 11. Open items (resolve during implementation)

- Exact **role** names and permission matrix (per module).
- **Sync conflict** rules per entity type.
- **Calendar dedupe** key (external id vs heuristic).
- **Price data** source for groceries (manual vs API).
- Python packaging (Poetry vs uv), RN E2E stack, local DB library (see ADR-002 when created).
- **Multi-family membership** (one vs many nodes per user) for v1.
- iOS/Android sideload and push certificate procedures.
- Whether a minimal **companion web** read-only view is desired later.

**Phase 2 complete:** [AGENTS.md](../AGENTS.md), [docs/standards/dependencies.md](standards/dependencies.md), `.cursor/rules/*.mdc`.

---

## 12. Decision log (approved baseline)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary client | React Native (TypeScript), sideloaded | Mobile-first, family use on phones |
| Backend | Python in Docker | Team preference; good for jobs and integrations |
| Server database | PostgreSQL | Multi-user, history, relational domains |
| Repo | Monorepo | Shared contract, one place for docs/CI |
| Deployment | Docker on home PC, LAN-only | Privacy and control until mini PC |
| Tenancy | Family/node isolation | Matches family sharing model |
| Calendar external | Import on user action, no overwrite | Safe merge with internal calendar |
| Offline | Local DB on mobile | Required for usability |
| Notifications | In-app + push | User requirement |
| Retention | Keep all history | User requirement |
| Guest access | None | User requirement |
| AI / voice / smart home | Deferred | Future updates |

---

## 13. Phase gate

**Phase 1:** Architecture — complete.  
**Phase 2:** Agent instructions — complete (`AGENTS.md`, `.cursor/rules/`).  
**Implementation (M0+):** Starts after explicit user go-ahead.
