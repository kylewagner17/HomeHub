import type { CalendarEventDto, CalendarEventKind } from '@homehub/shared';

import type { CalendarUiPrefs } from './calendarTypes';
import { DEFAULT_OWNER_PALETTE } from './calendarTypes';
import { inferEventKind } from './inferEventKind';

export type EventDisplayStyle = {
  kind: CalendarEventKind;
  symbol: string;
  color: string;
};

export function resolveEventKind(
  event: CalendarEventDto,
  kindOverrides: Record<string, CalendarEventKind>,
): CalendarEventKind {
  return kindOverrides[event.id] ?? inferEventKind(event);
}

export function ownerColor(ownerId: string, prefs: CalendarUiPrefs): string {
  if (prefs.ownerColors[ownerId]) {
    return prefs.ownerColors[ownerId];
  }
  let hash = 0;
  for (let i = 0; i < ownerId.length; i += 1) {
    hash = Math.imul(31, hash) + ownerId.charCodeAt(i);
    hash %= DEFAULT_OWNER_PALETTE.length;
  }
  return DEFAULT_OWNER_PALETTE[Math.abs(hash) % DEFAULT_OWNER_PALETTE.length];
}

export function displayForEvent(
  event: CalendarEventDto,
  prefs: CalendarUiPrefs,
  kindOverrides: Record<string, CalendarEventKind>,
): EventDisplayStyle {
  const kind = resolveEventKind(event, kindOverrides);
  const symbol = prefs.kindSymbols[kind] ?? prefs.kindSymbols.event;
  const color =
    prefs.colorMode === 'by_owner'
      ? ownerColor(event.owner_user_id, prefs)
      : (prefs.kindColors[kind] ?? prefs.kindColors.event);
  return { kind, symbol, color };
}
