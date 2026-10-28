# Dependencies — permitted stack and approval process

See also [architecture.md §9](../architecture.md).

## Approved baseline (add to lockfiles when M0 scaffolds apps)

### Python (`apps/api`)

| Package | Purpose |
|---------|---------|
| FastAPI | HTTP API |
| Uvicorn | ASGI server |
| Pydantic | Validation / settings |
| SQLAlchemy 2 | ORM |
| Alembic | Migrations |
| psycopg (or asyncpg) | PostgreSQL driver |
| PyJWT + bcrypt | Access tokens and password hashing |
| httpx | Outbound HTTP (OAuth, webhooks) |
| Ruff | Lint + format |
| PyJWT | Access tokens |
| bcrypt | Password hashing |
| email-validator | Pydantic `EmailStr` |

### Mobile (`apps/mobile`)

| Package | Purpose |
|---------|---------|
| React Native | App runtime |
| React Navigation | Navigation |
| TypeScript | Typing |
| ESLint + Prettier | Lint / format |
| @react-navigation/native, native-stack | App navigation (M1+) |
| react-native-screens | Navigation peer |
| react-native-keychain | Secure token storage |

### Infrastructure

| Package | Purpose |
|---------|---------|
| PostgreSQL 16+ (image) | Server database |
| Docker Compose | Local / home hosting |

## Conditionally approved (needs justification in PR)

| Package | When allowed |
|---------|----------------|
| Redis | Worker queue or pub/sub for realtime groceries — not before ADR |
| Celery | Heavy job volume — prefer APScheduler in-process first |
| `@op-engineering/op-sqlite` | Local DB (chosen in ADR-003) |
| `@react-native-community/netinfo` | Optional reconnect sync triggers |
| `@react-native-firebase/messaging` or equivalent | Push notifications |
| google-auth / MSAL libraries | Calendar OAuth import |

## Not approved without new ADR + user approval

- Next.js, Django, additional backend runtimes
- MongoDB, SQLite as server DB
- ORMs other than SQLAlchemy on API
- Global state libraries (Redux, MobX) unless existing code already uses one
- Heavy UI kits beyond what the mobile app already uses

## Adding a new dependency

1. Search the repo for an existing way to solve the problem.
2. Confirm the package is maintained, license-compatible, and LAN/offline constraints still hold.
3. Add to the correct app only (`apps/api` or `apps/mobile`), not root, unless shared tooling.
4. Pin in the app lockfile (`uv.lock`, `poetry.lock`, or `package-lock.json`).
5. Document in the PR: **why**, **alternatives rejected**, **size/security note**.
6. Update this file if the dependency becomes a standard part of the stack.

Agents: **do not add dependencies** for speculative future features. Ask the user if the task truly requires a package not listed above.
