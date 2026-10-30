# ADR-006: Reminders and push (M4)

## Status

Accepted — implements architecture M4.

## Context

HomeHub needs family-scoped reminders with optional recurrence, server-side scheduling, in-app notification delivery, and optional FCM push when configured.

## Decision

- **Data:** `reminders` (CRUD, soft delete), `reminder_fire_logs` (history of each fire), `user_notifications` (in-app inbox), `device_push_tokens` (auth module, one row per user/platform).
- **Recurrence:** Subset enum — `one_time` (legacy `none`), `daily`, `weekly`, `monthly`. Next fire computed in API (`reminders/recurrence.py`); no RRULE parser in M4.
- **Scheduler:** In-process **APScheduler** interval job in API lifespan (architecture §9); no Celery worker.
- **Tenancy:** All reminder routes require family membership; assignee `null` notifies all family members; assignee set notifies that user only (must be a member).
- **Push:** Best-effort FCM HTTP when `FCM_SERVER_KEY` is set; mobile registers token via `PUT /auth/device-token`. Without FCM, in-app polling satisfies “fires on device.”
- **Sync:** Reminders are online-first in M4 (no sync entity); a later milestone may add offline queue if needed.

## Consequences

- API process must stay running for fires (same as LAN hosting model).
- Full native push requires future mobile FCM SDK; server path is ready.
