import type { CalendarEventKind } from '@homehub/shared';

import type { CalendarUiPrefs } from '../features/calendar/calendarTypes';
import { defaultCalendarUiPrefs } from '../features/calendar/calendarTypes';
import { getDatabase } from './database';

function mergePrefs(raw: Partial<CalendarUiPrefs>): CalendarUiPrefs {
  const base = defaultCalendarUiPrefs();
  return {
    colorMode: raw.colorMode ?? base.colorMode,
    kindSymbols: { ...base.kindSymbols, ...raw.kindSymbols },
    kindColors: { ...base.kindColors, ...raw.kindColors },
    ownerColors: { ...base.ownerColors, ...raw.ownerColors },
  };
}

export function getCalendarUiPrefs(familyId: string): CalendarUiPrefs {
  const db = getDatabase();
  const result = db.executeSync('SELECT prefs_json FROM calendar_ui_prefs WHERE family_id = ?', [
    familyId,
  ]);
  const row = result.rows?.[0] as Record<string, unknown> | undefined;
  if (!row?.prefs_json) {
    return defaultCalendarUiPrefs();
  }
  return mergePrefs(JSON.parse(String(row.prefs_json)) as Partial<CalendarUiPrefs>);
}

export function saveCalendarUiPrefs(familyId: string, prefs: CalendarUiPrefs): void {
  const db = getDatabase();
  db.executeSync(
    `INSERT INTO calendar_ui_prefs (family_id, prefs_json) VALUES (?, ?)
     ON CONFLICT(family_id) DO UPDATE SET prefs_json = excluded.prefs_json`,
    [familyId, JSON.stringify(prefs)],
  );
}

export function getKindOverrides(): Record<string, CalendarEventKind> {
  const db = getDatabase();
  const result = db.executeSync('SELECT event_id, kind FROM calendar_event_kind_overrides');
  const map: Record<string, CalendarEventKind> = {};
  for (const row of result.rows ?? []) {
    const r = row as Record<string, unknown>;
    map[String(r.event_id)] = String(r.kind) as CalendarEventKind;
  }
  return map;
}

export function setKindOverride(eventId: string, kind: CalendarEventKind): void {
  const db = getDatabase();
  db.executeSync(
    `INSERT INTO calendar_event_kind_overrides (event_id, kind) VALUES (?, ?)
     ON CONFLICT(event_id) DO UPDATE SET kind = excluded.kind`,
    [eventId, kind],
  );
}
