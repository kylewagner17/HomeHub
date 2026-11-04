import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  FlatList,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import type {
  CalendarEventDto,
  CalendarEventKind,
  CalendarVisibility,
  FamilyMembershipSummary,
} from '@homehub/shared';

import {
  createCalendarEvent,
  deleteCalendarEvent,
  fetchCalendarEvents,
  fetchGoogleCalendarStatus,
  importCalendarGoogle,
  importCalendarIcs,
  updateCalendarEvent,
  ApiClientError,
} from '../../sync/apiClient';
import {
  getCalendarUiPrefs,
  getKindOverrides,
  setKindOverride,
} from '../../db/calendarPrefsStore';
import { displayForEvent, resolveEventKind } from './calendarDisplay';
import { CalendarSettingsModal } from './CalendarSettingsModal';
import { CALENDAR_KINDS, type CalendarUiPrefs } from './calendarTypes';
import {
  buildMonthGrid,
  endOfMonth,
  isoDateKey,
  monthLabel,
  startOfMonth,
  toUtcIsoFromLocalDateAndTime,
} from './calendarMonth';

type Props = {
  membership: FamilyMembershipSummary;
  onBack: () => void;
};

type ViewMode = 'list' | 'month';

export function CalendarScreen({ membership, onBack }: Props) {
  const [viewMode, setViewMode] = useState<ViewMode>('month');
  const [anchor, setAnchor] = useState(() => startOfMonth(new Date()));
  const [events, setEvents] = useState<CalendarEventDto[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState(isoDateKey(new Date()));
  const [showEditor, setShowEditor] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [title, setTitle] = useState('');
  const [icsText, setIcsText] = useState('');
  const [visibility, setVisibility] = useState<CalendarVisibility>('family');
  const [googleConnected, setGoogleConnected] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [uiPrefs, setUiPrefs] = useState<CalendarUiPrefs>(() => getCalendarUiPrefs(membership.family_id));
  const [kindOverrides, setKindOverrides] = useState<Record<string, CalendarEventKind>>(() =>
    getKindOverrides(),
  );
  const [editorKind, setEditorKind] = useState<CalendarEventKind>('event');

  const refreshDisplayPrefs = useCallback(() => {
    setUiPrefs(getCalendarUiPrefs(membership.family_id));
    setKindOverrides(getKindOverrides());
  }, [membership.family_id]);

  const range = useMemo(() => {
    const start = startOfMonth(anchor);
    const end = endOfMonth(anchor);
    return { start: start.toISOString(), end: end.toISOString() };
  }, [anchor]);

  const reload = useCallback(async () => {
    const list = await fetchCalendarEvents(membership.family_id, range.start, range.end);
    setEvents(list);
  }, [membership.family_id, range.end, range.start]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await reload();
        const status = await fetchGoogleCalendarStatus();
        if (!cancelled) {
          setGoogleConnected(status.connected);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [reload]);

  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEventDto[]>();
    for (const ev of events) {
      const key = isoDateKey(new Date(ev.starts_at));
      const bucket = map.get(key) ?? [];
      bucket.push(ev);
      map.set(key, bucket);
    }
    return map;
  }, [events]);

  const listData = useMemo(() => {
    return [...events].sort(
      (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
    );
  }, [events]);

  const dayEvents = eventsByDay.get(selectedDay) ?? [];

  function openCreate() {
    setEditId(null);
    setTitle('');
    setVisibility('family');
    setEditorKind('event');
    setShowEditor(true);
  }

  function openEdit(ev: CalendarEventDto) {
    setEditId(ev.id);
    setTitle(ev.title);
    setVisibility(ev.visibility);
    setEditorKind(resolveEventKind(ev, kindOverrides));
    setSelectedDay(isoDateKey(new Date(ev.starts_at)));
    setShowEditor(true);
  }

  function renderEventTitle(ev: CalendarEventDto) {
    const style = displayForEvent(ev, uiPrefs, kindOverrides);
    return (
      <Text style={[styles.eventTitle, { color: style.color }]}>
        {style.symbol} {ev.title}
      </Text>
    );
  }

  async function saveEvent() {
    const trimmed = title.trim();
    if (!trimmed) {
      return;
    }
    const starts = toUtcIsoFromLocalDateAndTime(selectedDay, 9, 0);
    const ends = toUtcIsoFromLocalDateAndTime(selectedDay, 10, 0);
    if (editId) {
      await updateCalendarEvent(membership.family_id, editId, {
        title: trimmed,
        starts_at: starts,
        ends_at: ends,
        visibility,
      });
      setKindOverride(editId, editorKind);
    } else {
      const created = await createCalendarEvent(membership.family_id, {
        title: trimmed,
        starts_at: starts,
        ends_at: ends,
        visibility,
      });
      setKindOverride(created.id, editorKind);
    }
    refreshDisplayPrefs();
    setShowEditor(false);
    await reload();
  }

  async function removeEvent(id: string) {
    await deleteCalendarEvent(membership.family_id, id);
    await reload();
  }

  async function runIcalImport() {
    const result = await importCalendarIcs(membership.family_id, icsText);
    Alert.alert(
      'Import complete',
      `Added ${result.imported}, skipped ${result.skipped_duplicates} duplicates`,
    );
    setShowImport(false);
    setIcsText('');
    await reload();
  }

  async function runGoogleImport() {
    if (!googleConnected) {
      Alert.alert(
        'Google not connected',
        'Set GOOGLE_OAUTH_CLIENT_ID on the server, then connect via POST /integrations/google/connect with your OAuth code (mobile deep link flow coming soon). Apple Calendar: export .ics and paste below.',
      );
      return;
    }
    try {
      const result = await importCalendarGoogle(membership.family_id, range.start, range.end);
      Alert.alert(
        'Google import',
        `Added ${result.imported}, skipped ${result.skipped_duplicates} duplicates.\n\n` +
          `Range: ${monthLabel(anchor)} only. Includes checked calendars in Google (not Tasks). ` +
          'Re-import other months with Prev/Next first.',
      );
      await reload();
    } catch (err) {
      const message =
        err instanceof ApiClientError
          ? `${err.code}: ${err.message}`
          : 'Google import failed';
      Alert.alert('Google import failed', message);
    }
  }

  const grid = buildMonthGrid(anchor);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Button title="Back" onPress={onBack} />
        <Text style={styles.heading}>Calendar</Text>
        <Pressable
          accessibilityLabel="Calendar display settings"
          onPress={() => setShowSettings(true)}
          style={styles.gearButton}>
          <Text style={styles.gearIcon}>⚙</Text>
        </Pressable>
      </View>
      <View style={styles.toggleRow}>
        <Pressable
          style={[styles.toggle, viewMode === 'month' && styles.toggleActive]}
          onPress={() => setViewMode('month')}>
          <Text>Month</Text>
        </Pressable>
        <Pressable
          style={[styles.toggle, viewMode === 'list' && styles.toggleActive]}
          onPress={() => setViewMode('list')}>
          <Text>List</Text>
        </Pressable>
      </View>
      <View style={styles.navRow}>
        <Button
          title="Prev"
          onPress={() =>
            setAnchor(prev => new Date(prev.getFullYear(), prev.getMonth() - 1, 1))
          }
        />
        <Text style={styles.monthLabel}>{monthLabel(anchor)}</Text>
        <Button
          title="Next"
          onPress={() =>
            setAnchor(prev => new Date(prev.getFullYear(), prev.getMonth() + 1, 1))
          }
        />
      </View>
      {loading ? (
        <Text style={styles.meta}>Loading…</Text>
      ) : viewMode === 'month' ? (
        <ScrollView>
          <View style={styles.weekRow}>
            {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(d => (
              <Text key={d} style={styles.weekDay}>
                {d}
              </Text>
            ))}
          </View>
          <View style={styles.grid}>
            {grid.map(cell => {
              const dayList = eventsByDay.get(cell.isoDate) ?? [];
              const selected = cell.isoDate === selectedDay;
              return (
                <Pressable
                  key={cell.isoDate}
                  style={[
                    styles.cell,
                    !cell.inCurrentMonth && styles.cellMuted,
                    selected && styles.cellSelected,
                  ]}
                  onPress={() => setSelectedDay(cell.isoDate)}>
                  <Text style={styles.cellDay}>{cell.date.getDate()}</Text>
                  <View style={styles.dotRow}>
                    {dayList.slice(0, 3).map(ev => {
                      const { color } = displayForEvent(ev, uiPrefs, kindOverrides);
                      return (
                        <View key={ev.id} style={[styles.dot, { backgroundColor: color }]} />
                      );
                    })}
                  </View>
                </Pressable>
              );
            })}
          </View>
          <Text style={styles.sectionTitle}>{selectedDay}</Text>
          {dayEvents.map(ev => (
            <Pressable key={ev.id} style={styles.eventCard} onPress={() => openEdit(ev)}>
              {renderEventTitle(ev)}
              <Text style={styles.eventMeta}>
                {new Date(ev.starts_at).toLocaleString()} · {ev.visibility}
              </Text>
              <Button title="Delete" onPress={() => removeEvent(ev.id)} />
            </Pressable>
          ))}
        </ScrollView>
      ) : (
        <FlatList
          data={listData}
          keyExtractor={item => item.id}
          renderItem={({ item }) => (
            <Pressable style={styles.eventCard} onPress={() => openEdit(item)}>
              {renderEventTitle(item)}
              <Text style={styles.eventMeta}>{new Date(item.starts_at).toLocaleString()}</Text>
            </Pressable>
          )}
          ListEmptyComponent={<Text style={styles.meta}>No events this month</Text>}
        />
      )}
      <View style={styles.actions}>
        <Button title="Add event" onPress={openCreate} />
        <Button title="Import .ics" onPress={() => setShowImport(true)} />
        <Button title="Import Google" onPress={() => runGoogleImport()} />
      </View>

      <Modal visible={showEditor} animationType="slide">
        <View style={styles.modal}>
          <Text style={styles.heading}>{editId ? 'Edit event' : 'New event'}</Text>
          <TextInput
            style={styles.input}
            placeholder="Title"
            value={title}
            onChangeText={setTitle}
          />
          <Text style={styles.meta}>Date: {selectedDay}</Text>
          <View style={styles.toggleRow}>
            {(['family', 'personal'] as CalendarVisibility[]).map(v => (
              <Pressable
                key={v}
                style={[styles.toggle, visibility === v && styles.toggleActive]}
                onPress={() => setVisibility(v)}>
                <Text>{v}</Text>
              </Pressable>
            ))}
          </View>
          <Text style={styles.meta}>Event type (symbol)</Text>
          <View style={styles.toggleRow}>
            {CALENDAR_KINDS.map(k => (
              <Pressable
                key={k}
                style={[styles.toggle, editorKind === k && styles.toggleActive]}
                onPress={() => setEditorKind(k)}>
                <Text>
                  {uiPrefs.kindSymbols[k]} {k}
                </Text>
              </Pressable>
            ))}
          </View>
          <Button title="Save" onPress={() => saveEvent().catch(() => undefined)} />
          <Button title="Cancel" onPress={() => setShowEditor(false)} />
        </View>
      </Modal>

      <Modal visible={showImport} animationType="slide">
        <View style={styles.modal}>
          <Text style={styles.heading}>Import iCalendar (.ics)</Text>
          <Text style={styles.meta}>
            Apple Calendar: File → Export → paste contents. Existing HomeHub events are never
            overwritten; duplicates are skipped.
          </Text>
          <TextInput
            style={[styles.input, styles.icsInput]}
            multiline
            placeholder="Paste .ics text"
            value={icsText}
            onChangeText={setIcsText}
          />
          <Button title="Import" onPress={() => runIcalImport().catch(() => undefined)} />
          <Button title="Close" onPress={() => setShowImport(false)} />
        </View>
      </Modal>

      <CalendarSettingsModal
        visible={showSettings}
        familyId={membership.family_id}
        onClose={() => setShowSettings(false)}
        onSaved={refreshDisplayPrefs}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 48, paddingHorizontal: 12 },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  heading: { fontSize: 20, fontWeight: '600', flex: 1, marginLeft: 8 },
  gearButton: { padding: 8 },
  gearIcon: { fontSize: 22 },
  toggleRow: { flexDirection: 'row', gap: 8, marginBottom: 8 },
  toggle: { paddingHorizontal: 12, paddingVertical: 6, backgroundColor: '#eee', borderRadius: 6 },
  toggleActive: { backgroundColor: '#cce5ff' },
  navRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  monthLabel: { fontSize: 16, fontWeight: '500' },
  weekRow: { flexDirection: 'row', marginTop: 8 },
  weekDay: { flex: 1, textAlign: 'center', fontSize: 11, color: '#666' },
  grid: { flexDirection: 'row', flexWrap: 'wrap' },
  cell: {
    width: `${100 / 7}%`,
    aspectRatio: 1,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: '#ddd',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cellMuted: { backgroundColor: '#fafafa' },
  cellSelected: { backgroundColor: '#e8f4ff' },
  cellDay: { fontSize: 14 },
  dotRow: { flexDirection: 'row', gap: 2, marginTop: 2 },
  dot: { width: 6, height: 6, borderRadius: 3 },
  sectionTitle: { marginTop: 12, fontWeight: '600' },
  eventCard: {
    padding: 12,
    backgroundColor: '#f4f4f4',
    borderRadius: 8,
    marginVertical: 4,
  },
  eventTitle: { fontSize: 16, fontWeight: '500' },
  eventMeta: { fontSize: 12, color: '#666', marginTop: 4 },
  meta: { color: '#666', marginVertical: 8 },
  actions: { gap: 8, marginVertical: 12 },
  modal: { flex: 1, padding: 24, paddingTop: 48 },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    marginVertical: 8,
  },
  icsInput: { minHeight: 160, textAlignVertical: 'top' },
});
