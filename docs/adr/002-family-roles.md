# ADR-002: Family roles (M1)

## Status

Accepted

## Decision

| Role | API value | Dashboard (M1 shell) |
|------|-----------|----------------------|
| Parent / admin | `admin` | Full family modules: calendar, groceries, maintenance, planning, reminders |
| Child / member | `member` | Limited: assigned tasks, personal calendar (placeholders only in M1) |

- First user who **creates** a family receives `admin`.
- Users who **join** via invite code receive `member`.
- Only `admin` may change another member's role (`PATCH .../members/{id}/role`).

## Consequences

- Authorization for future modules checks `FamilyRole` on the active family context.
- Mobile dashboard reads `role` from `GET /auth/me` for the selected family.
