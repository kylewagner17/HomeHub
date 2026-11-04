import type { CalendarEventKind } from '@homehub/shared';

export type CalendarColorMode = 'by_owner' | 'by_kind';

export type CalendarUiPrefs = {
  colorMode: CalendarColorMode;
  kindSymbols: Record<CalendarEventKind, string>;
  kindColors: Record<CalendarEventKind, string>;
  ownerColors: Record<string, string>;
};

export const CALENDAR_KINDS: CalendarEventKind[] = ['event', 'meeting', 'birthday', 'task'];

export const DEFAULT_OWNER_PALETTE = [
  '#1976d2',
  '#2e7d32',
  '#c2185b',
  '#ed6c02',
  '#6a1b9a',
  '#00838f',
];

export function defaultCalendarUiPrefs(): CalendarUiPrefs {
  return {
    colorMode: 'by_owner',
    kindSymbols: {
      event: '●',
      meeting: '📅',
      birthday: '🎂',
      task: '☑',
    },
    kindColors: {
      event: '#1976d2',
      meeting: '#2e7d32',
      birthday: '#c2185b',
      task: '#ed6c02',
    },
    ownerColors: {},
  };
}
