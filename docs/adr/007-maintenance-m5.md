# ADR-007: Maintenance tracker (M5)

## Status

Accepted.

## Context

Families track home and auto maintenance with different fields, completion history, and due dates. Reminders should use the existing M4 scheduler and notification pipeline.

## Decision

- **Data:** `maintenance_items` (active schedule + type-specific fields), `maintenance_completions` (immutable history).
- **Categories:** `home` and `auto` tabs; **item kinds** (`hvac_filter`, `oil_change`, etc.) drive which fields are required.
- **Next due:** Computed in API (`maintenance/scheduling.py`) on create/update/complete — date intervals, mileage intervals, or both (due when **either** threshold is reached for display; reminder fires on **next due date** when set).
- **Reminders:** Each active item may link to a `reminders` row (`one_time` at `next_due_at`); maintenance service calls `RemindersService.upsert_maintenance_reminder` — no duplicated scheduler logic.
- **Online-first:** No sync entity in M5 (same as reminders M4).

## Consequences

- Mileage-only due items need a `next_due_at` for push/in-app unless user sets an estimated due date on complete.
- Completing an item without `interval_days` leaves date reminder disabled until user sets the next due date.
