/** Month grid helpers for calendar month view (local timezone). */

export type MonthCell = {
  date: Date;
  inCurrentMonth: boolean;
  isoDate: string;
};

export function startOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

export function endOfMonth(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0, 23, 59, 59, 999);
}

export function isoDateKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

export function buildMonthGrid(anchor: Date): MonthCell[] {
  const first = startOfMonth(anchor);
  const start = new Date(first);
  start.setDate(first.getDate() - first.getDay());
  const cells: MonthCell[] = [];
  for (let i = 0; i < 42; i += 1) {
    const date = new Date(start);
    date.setDate(start.getDate() + i);
    cells.push({
      date,
      inCurrentMonth: date.getMonth() === anchor.getMonth(),
      isoDate: isoDateKey(date),
    });
  }
  return cells;
}

export function monthLabel(anchor: Date): string {
  return anchor.toLocaleString(undefined, { month: 'long', year: 'numeric' });
}

export function toUtcIsoFromLocalDateAndTime(
  dateKey: string,
  hours: number,
  minutes: number,
): string {
  const [y, m, d] = dateKey.split('-').map(Number);
  const local = new Date(y, m - 1, d, hours, minutes, 0, 0);
  return local.toISOString();
}
