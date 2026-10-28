# ADR-003: Sync protocol and local database (M2)

## Status

Accepted

## Local database (mobile)

**Choice:** `@op-engineering/op-sqlite` — SQLite on device with a small schema in `apps/mobile/src/db/`.

## Conflict policy (grocery lists, M2)

| Situation | Resolution |
|-----------|------------|
| Same `idempotency_key` replayed | Server ignores duplicate; client clears outbox entry |
| Client `revision` &lt; server `revision` on upsert | **Server wins** — response includes server row; client overwrites local |
| Client `revision` = server `revision` | Apply payload if changed fields; bump revision |
| Client `revision` &gt; server `revision` | Accept client upsert; server sets `revision` to client value |
| Delete | Soft-delete (`deleted_at`); tombstones included in pull |
| Permissions | Family membership required; server authoritative |

M3 may add realtime push; M2 is **pull after push** and on app foreground / network reconnect.

## Sync API

- `GET /api/v1/sync/ping` — authenticated liveness
- `POST /api/v1/sync/push` — apply outbox mutations
- `GET /api/v1/sync/pull` — changes since `since` (ISO-8601 UTC)

Entity type in M2: `grocery_list` only.
