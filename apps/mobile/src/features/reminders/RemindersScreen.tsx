import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Alert,
  Button,
  FlatList,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import type { FamilyMembershipSummary, ReminderDto, ReminderRecurrence } from '@homehub/shared';

import {
  createReminder,
  deleteReminder,
  fetchNotifications,
  fetchReminderHistory,
  fetchReminders,
  markNotificationRead,
  registerDeviceToken,
} from '../../sync/apiClient';
import {
  defaultReminderTime,
  formatReminderDateTime,
  nextFireAtFrom12hTime,
  recurrenceLabel,
  type Meridiem,
  type ReminderTimeFields,
} from './reminderSchedule';

type Props = {
  membership: FamilyMembershipSummary;
  onBack: () => void;
};

const RECURRENCE_OPTIONS: ReminderRecurrence[] = ['one_time', 'daily', 'weekly', 'monthly'];
const MERIDIEM_OPTIONS: Meridiem[] = ['AM', 'PM'];

export function RemindersScreen({ membership, onBack }: Props) {
  const [reminders, setReminders] = useState<ReminderDto[]>([]);
  const [history, setHistory] = useState<{ id: string; title: string; fired_at: string }[]>([]);
  const [title, setTitle] = useState('');
  const [timeFields, setTimeFields] = useState<ReminderTimeFields>(defaultReminderTime);
  const [timeError, setTimeError] = useState<string | null>(null);
  const [recurrence, setRecurrence] = useState<ReminderRecurrence>('one_time');
  const [loading, setLoading] = useState(true);
  const lastPollRef = useRef<string | undefined>(undefined);
  const seenNotificationIds = useRef(new Set<string>());

  const reload = useCallback(async () => {
    const [list, hist] = await Promise.all([
      fetchReminders(membership.family_id),
      fetchReminderHistory(membership.family_id),
    ]);
    setReminders(list);
    setHistory(hist.map(h => ({ id: h.id, title: h.title, fired_at: h.fired_at })));
  }, [membership.family_id]);

  const pollNotifications = useCallback(async () => {
    const items = await fetchNotifications(lastPollRef.current);
    for (const item of items) {
      if (seenNotificationIds.current.has(item.id)) {
        continue;
      }
      seenNotificationIds.current.add(item.id);
      if (item.read_at) {
        continue;
      }
      Alert.alert('Reminder', item.body ? `${item.title}\n${item.body}` : item.title, [
        {
          text: 'OK',
          onPress: () => {
            markNotificationRead(item.id).catch(() => undefined);
          },
        },
      ]);
    }
    if (items.length > 0) {
      lastPollRef.current = items[0].created_at;
    }
  }, []);

  useEffect(() => {
    registerDeviceToken(Platform.OS === 'ios' ? 'ios' : 'android', 'local-emulator').catch(
      () => undefined,
    );
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await reload();
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

  useEffect(() => {
    pollNotifications().catch(() => undefined);
    const id = setInterval(() => {
      pollNotifications().catch(() => undefined);
      reload().catch(() => undefined);
    }, 15_000);
    return () => clearInterval(id);
  }, [pollNotifications, reload]);

  async function onAdd() {
    const trimmed = title.trim();
    if (!trimmed) {
      return;
    }
    const schedule = nextFireAtFrom12hTime(timeFields);
    if (!schedule.ok) {
      setTimeError(schedule.message);
      return;
    }
    setTimeError(null);
    await createReminder(membership.family_id, {
      title: trimmed,
      recurrence,
      next_fire_at: schedule.iso,
    });
    setTitle('');
    setTimeFields(defaultReminderTime());
    await reload();
  }

  async function onDelete(reminderId: string) {
    await deleteReminder(membership.family_id, reminderId);
    await reload();
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <Text>Loading reminders…</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Button title="Back" onPress={onBack} />
        <Text style={styles.title}>Reminders</Text>
      </View>
      <Text style={styles.section}>New reminder</Text>
      <Text style={styles.hint}>Time uses today&apos;s date; calendar date picking comes later.</Text>
      <TextInput
        style={styles.input}
        placeholder="Title"
        value={title}
        onChangeText={setTitle}
      />
      <Text style={styles.fieldLabel}>Trigger time</Text>
      <View style={styles.timeRow}>
        <TextInput
          style={[styles.input, styles.timePart]}
          placeholder="12"
          value={timeFields.hour12}
          onChangeText={hour12 => {
            setTimeFields(prev => ({ ...prev, hour12 }));
            setTimeError(null);
          }}
          keyboardType="number-pad"
          maxLength={2}
        />
        <Text style={styles.timeColon}>:</Text>
        <TextInput
          style={[styles.input, styles.timePart]}
          placeholder="00"
          value={timeFields.minute}
          onChangeText={minute => {
            setTimeFields(prev => ({ ...prev, minute }));
            setTimeError(null);
          }}
          keyboardType="number-pad"
          maxLength={2}
        />
        <View style={styles.meridiemRow}>
          {MERIDIEM_OPTIONS.map(option => (
            <Pressable
              key={option}
              style={[styles.chip, timeFields.meridiem === option && styles.chipActive]}
              onPress={() => {
                setTimeFields(prev => ({ ...prev, meridiem: option }));
                setTimeError(null);
              }}>
              <Text style={styles.chipText}>{option}</Text>
            </Pressable>
          ))}
        </View>
      </View>
      {timeError ? <Text style={styles.error}>{timeError}</Text> : null}
      <View style={styles.recurrenceRow}>
        {RECURRENCE_OPTIONS.map(option => (
          <Pressable
            key={option}
            style={[styles.chip, recurrence === option && styles.chipActive]}
            onPress={() => setRecurrence(option)}>
            <Text style={styles.chipText}>{recurrenceLabel(option)}</Text>
          </Pressable>
        ))}
      </View>
      <Button title="Add reminder" onPress={() => onAdd().catch(() => undefined)} />

      <Text style={styles.section}>Upcoming</Text>
      <FlatList
        data={reminders}
        keyExtractor={item => item.id}
        ListEmptyComponent={<Text style={styles.empty}>No reminders yet.</Text>}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <View style={styles.rowBody}>
              <Text style={styles.rowTitle}>{item.title}</Text>
              <Text style={styles.rowMeta}>
                {formatReminderDateTime(item.next_fire_at)} · {recurrenceLabel(item.recurrence)}
                {item.enabled ? '' : ' · done'}
              </Text>
            </View>
            <Button title="Delete" onPress={() => onDelete(item.id).catch(() => undefined)} />
          </View>
        )}
      />

      <Text style={styles.section}>History</Text>
      <FlatList
        data={history}
        keyExtractor={item => item.id}
        ListEmptyComponent={<Text style={styles.empty}>Nothing fired yet.</Text>}
        renderItem={({ item }) => (
          <Text style={styles.historyRow}>
            {formatReminderDateTime(item.fired_at)} — {item.title}
          </Text>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, paddingTop: 48 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  title: { fontSize: 22, fontWeight: '600', flex: 1 },
  section: { fontSize: 16, fontWeight: '600', marginTop: 16, marginBottom: 8 },
  hint: { fontSize: 12, color: '#666', marginBottom: 8 },
  fieldLabel: { fontSize: 14, marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
  },
  error: { color: '#b00020', marginBottom: 8 },
  timeRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 6 },
  timePart: { flex: 0, width: 56, marginBottom: 0, textAlign: 'center' },
  timeColon: { fontSize: 18, fontWeight: '600' },
  meridiemRow: { flexDirection: 'row', gap: 6, marginLeft: 4 },
  recurrenceRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#eee',
  },
  chipActive: { backgroundColor: '#cde' },
  chipText: { fontSize: 12 },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#ddd',
  },
  rowBody: { flex: 1, paddingRight: 8 },
  rowTitle: { fontSize: 16, fontWeight: '500' },
  rowMeta: { fontSize: 12, color: '#666', marginTop: 2 },
  historyRow: { fontSize: 14, color: '#444', marginBottom: 6 },
  empty: { color: '#888', fontStyle: 'italic' },
});
