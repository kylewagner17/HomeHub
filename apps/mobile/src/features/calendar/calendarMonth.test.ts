import { buildMonthGrid, isoDateKey } from './calendarMonth';

describe('calendarMonth', () => {
  it('builds 42 cells for a month grid', () => {
    const grid = buildMonthGrid(new Date(2026, 10, 15));
    expect(grid).toHaveLength(42);
    expect(grid.some(c => c.inCurrentMonth)).toBe(true);
  });

  it('formats iso date keys', () => {
    expect(isoDateKey(new Date(2026, 0, 5))).toBe('2026-01-05');
  });
});
