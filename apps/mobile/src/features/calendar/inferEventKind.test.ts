import type { CalendarEventDto } from '@homehub/shared';

import { inferEventKind } from './inferEventKind';

const baseEvent = (title: string, extra: Partial<CalendarEventDto> = {}): CalendarEventDto => ({
  id: '1',
  family_id: 'f',
  owner_user_id: 'u',
  title,
  description: null,
  location: null,
  starts_at: '2026-11-01T12:00:00Z',
  ends_at: '2026-11-01T13:00:00Z',
  all_day: false,
  timezone: null,
  visibility: 'family',
  external_provider: null,
  external_uid: null,
  created_at: '2026-11-01T00:00:00Z',
  updated_at: '2026-11-01T00:00:00Z',
  ...extra,
});

describe('inferEventKind', () => {
  it('detects birthdays', () => {
    expect(inferEventKind(baseEvent("Mom's birthday"))).toBe('birthday');
  });

  it('detects meetings', () => {
    expect(inferEventKind(baseEvent('Team standup sync'))).toBe('meeting');
  });

  it('detects tasks', () => {
    expect(inferEventKind(baseEvent('[task] Buy milk'))).toBe('task');
  });
});
