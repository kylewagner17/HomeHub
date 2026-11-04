import type { CalendarEventDto, CalendarEventKind } from '@homehub/shared';

/** Heuristic kind for imported / untyped events (display only unless overridden locally). */
export function inferEventKind(event: CalendarEventDto): CalendarEventKind {
  const title = event.title.toLowerCase();
  const external = `${event.external_provider ?? ''} ${event.external_uid ?? ''}`.toLowerCase();

  if (
    external.includes('birthday') ||
    external.includes('#contacts@') ||
    /\bbirthday\b|\bbday\b|\bturns \d+/.test(title)
  ) {
    return 'birthday';
  }
  if (/^task:|^\[task\]|^\u2610|\u2611|todo:/i.test(event.title) || /\btask\b/.test(title)) {
    return 'task';
  }
  if (
    /\b(meeting|interview|standup|sync|zoom|teams|google meet|conference|call with)\b/.test(title)
  ) {
    return 'meeting';
  }
  return 'event';
}
