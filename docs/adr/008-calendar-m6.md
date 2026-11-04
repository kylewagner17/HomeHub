# ADR-008: Calendar and import (M6)

## Status

Accepted — implements architecture M6.

## Context

Families need an internal calendar with personal vs family visibility, CRUD, and non-destructive import from external calendars (Google OAuth, iCal for Apple/Outlook exports).

## Decisions

- **Online-first:** Calendar events live on the API (same pattern as reminders M4); mobile fetches on screen focus.
- **Import policy:** External import **never updates** existing HomeHub rows. Skip when `external_uid` + provider match, or when start/end/title heuristic matches (±1 minute on start).
- **Providers:** `google` (Calendar API v3 via httpx + stored OAuth tokens), `ical` (paste/upload `.ics` text). Apple Calendar uses export → iCal import.
- **Google scope:** All calendars **selected** in the user’s Google Calendar sidebar (not `primary` only). Unchecked calendars are skipped. **Google Tasks** are not calendar events and are not imported.
- **Dedupe key:** Prefer `external_uid` from VEVENT UID or Google `id`; fallback heuristic for legacy rows without UID.
- **Reminders:** Remain separate entities; calendar does not auto-create reminders in M6 (future link optional).

## Consequences

- Google import requires `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET` in API env.
- No new Python dependencies; iCal parsing is a minimal in-repo parser for VEVENT fields.
