/** Build next_fire_at from local 12h time until calendar date picking lands in M6. */

export type Meridiem = 'AM' | 'PM';

export type ReminderTimeFields = {
  hour12: string;
  minute: string;
  meridiem: Meridiem;
};

export type TimeParseResult =
  | { ok: true; iso: string }
  | { ok: false; message: string };

/** Default trigger time: five minutes from now (local, 12h). */
export function defaultReminderTime(): ReminderTimeFields {
  const d = new Date();
  d.setMinutes(d.getMinutes() + 5);
  d.setSeconds(0, 0);
  return dateToReminderTimeFields(d);
}

export function dateToReminderTimeFields(date: Date): ReminderTimeFields {
  const hours24 = date.getHours();
  const meridiem: Meridiem = hours24 >= 12 ? 'PM' : 'AM';
  let hour12 = hours24 % 12;
  if (hour12 === 0) {
    hour12 = 12;
  }
  return {
    hour12: String(hour12),
    minute: String(date.getMinutes()).padStart(2, '0'),
    meridiem,
  };
}

function to24Hour(hour12: number, meridiem: Meridiem): number {
  if (meridiem === 'AM') {
    return hour12 === 12 ? 0 : hour12;
  }
  return hour12 === 12 ? 12 : hour12 + 12;
}

/**
 * Parse 12h clock fields and return ISO UTC for the next occurrence (today or tomorrow local).
 */
export function nextFireAtFrom12hTime(
  fields: ReminderTimeFields,
  now = new Date(),
): TimeParseResult {
  const hourText = fields.hour12.trim();
  const minuteText = fields.minute.trim();
  if (!/^\d{1,2}$/.test(hourText) || !/^\d{1,2}$/.test(minuteText)) {
    return { ok: false, message: 'Enter hour and minute as numbers' };
  }
  const hour12 = Number(hourText);
  const minutes = Number(minuteText);
  if (hour12 < 1 || hour12 > 12) {
    return { ok: false, message: 'Hour must be 1–12' };
  }
  if (minutes < 0 || minutes > 59) {
    return { ok: false, message: 'Minutes must be 0–59' };
  }

  const hours24 = to24Hour(hour12, fields.meridiem);
  const candidate = new Date(now);
  candidate.setHours(hours24, minutes, 0, 0);
  if (candidate.getTime() <= now.getTime()) {
    candidate.setDate(candidate.getDate() + 1);
  }
  return { ok: true, iso: candidate.toISOString() };
}

/** Time only, e.g. `2:05 PM`. */
export function formatTime12h(date: Date): string {
  const fields = dateToReminderTimeFields(date);
  return `${fields.hour12}:${fields.minute} ${fields.meridiem}`;
}

/** Date + 12h time for list rows, e.g. `Oct 30, 2026 at 2:05 PM`. */
export function formatReminderDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  const datePart = date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  return `${datePart} at ${formatTime12h(date)}`;
}

export const RECURRENCE_LABELS: Record<
  import('@homehub/shared').ReminderRecurrence | 'none',
  string
> = {
  one_time: 'One time',
  none: 'One time',
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
};

export function recurrenceLabel(value: string): string {
  return RECURRENCE_LABELS[value as keyof typeof RECURRENCE_LABELS] ?? value;
}
