import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import type {
  FamilyMembershipSummary,
  MaintenanceCategory,
  MaintenanceItemDto,
  MaintenanceItemKind,
  StockStatus,
} from '@homehub/shared';

import {
  completeMaintenanceItem,
  createMaintenanceItem,
  deleteMaintenanceItem,
  fetchMaintenanceHistory,
  fetchMaintenanceItems,
  fetchNotifications,
  markNotificationRead,
  setMaintenanceStockStatus,
} from '../../sync/apiClient';
import { runSync } from '../../sync/syncEngine';
import { formatReminderDateTime } from '../reminders/reminderSchedule';

type Props = {
  membership: FamilyMembershipSummary;
  onBack: () => void;
};

const HOME_KINDS: MaintenanceItemKind[] = [
  'hvac_filter',
  'water_filter',
  'smoke_detector',
  'generic_home',
];

const AUTO_KINDS: MaintenanceItemKind[] = ['oil_change', 'tire_rotation', 'generic_auto'];

const KIND_LABELS: Record<MaintenanceItemKind, string> = {
  hvac_filter: 'HVAC filter',
  water_filter: 'Water filter',
  smoke_detector: 'Smoke detector',
  generic_home: 'Other home',
  oil_change: 'Oil change',
  tire_rotation: 'Tire rotation',
  generic_auto: 'Other auto',
  consumable: 'Household item',
};

const STOCK_LABELS = {
  in_stock: 'In stock',
  low: 'Low',
  out: 'Out',
} as const;

function parseOptionalDate(isoDate: string): string | undefined {
  const trimmed = isoDate.trim();
  if (!trimmed) {
    return undefined;
  }
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trimmed);
  if (!match) {
    return undefined;
  }
  return new Date(`${trimmed}T12:00:00`).toISOString();
}

export function MaintenanceScreen({ membership, onBack }: Props) {
  const [tab, setTab] = useState<MaintenanceCategory>('home');
  const [items, setItems] = useState<MaintenanceItemDto[]>([]);
  const [historyCount, setHistoryCount] = useState(0);
  const [title, setTitle] = useState('');
  const [itemKind, setItemKind] = useState<MaintenanceItemKind>('hvac_filter');
  const [intervalMiles, setIntervalMiles] = useState('5000');
  const [nextDueDate, setNextDueDate] = useState('');
  const [completeNextDueDate, setCompleteNextDueDate] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [completeItemId, setCompleteItemId] = useState<string | null>(null);
  const [completeMileage, setCompleteMileage] = useState('');

  const kinds = useMemo(
    (): MaintenanceItemKind[] =>
      tab === 'home' ? HOME_KINDS : tab === 'auto' ? AUTO_KINDS : [],
    [tab],
  );

  const reload = useCallback(async () => {
    const [list, history] = await Promise.all([
      fetchMaintenanceItems(membership.family_id, tab),
      fetchMaintenanceHistory(membership.family_id),
    ]);
    setItems(list);
    setHistoryCount(history.length);
  }, [membership.family_id, tab]);

  useEffect(() => {
    if (kinds.length > 0) {
      setItemKind(kinds[0]);
    }
  }, [tab, kinds]);

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
    const poll = async () => {
      const notes = await fetchNotifications();
      for (const note of notes) {
        if (note.read_at || !note.title.startsWith('Maintenance:')) {
          continue;
        }
        Alert.alert('Maintenance reminder', note.title, [
          {
            text: 'OK',
            onPress: () => markNotificationRead(note.id).catch(() => undefined),
          },
        ]);
      }
    };
    poll().catch(() => undefined);
    const id = setInterval(() => poll().catch(() => undefined), 20_000);
    return () => clearInterval(id);
  }, []);

  async function onAdd() {
    const trimmed = title.trim();
    if (!trimmed) {
      setFormError('Title is required');
      return;
    }
    setFormError(null);
    if (tab === 'items') {
      await createMaintenanceItem(membership.family_id, {
        category: 'items',
        item_kind: 'consumable',
        title: trimmed,
      });
      setTitle('');
      await reload();
      return;
    }
    const parsedDue = nextDueDate ? parseOptionalDate(nextDueDate) : undefined;
    if (nextDueDate.trim() && !parsedDue) {
      setFormError('Use due date format YYYY-MM-DD');
      return;
    }
    const payload: Record<string, unknown> = {
      category: tab,
      item_kind: itemKind,
      title: trimmed,
    };
    if (tab === 'auto') {
      payload.interval_miles = Number(intervalMiles) || undefined;
    }
    if (parsedDue) {
      payload.next_due_at = parsedDue;
    }
    await createMaintenanceItem(membership.family_id, payload);
    setTitle('');
    setNextDueDate('');
    await reload();
  }

  async function onComplete(item: MaintenanceItemDto) {
    if (item.category === 'auto') {
      setCompleteItemId(item.id);
      setCompleteMileage(
        item.current_mileage?.toString() ??
          item.mileage_at_last_service?.toString() ??
          '',
      );
      return;
    }
    const payload: Record<string, unknown> = {
      completed_at: new Date().toISOString(),
    };
    if (completeNextDueDate.trim()) {
      const parsed = parseOptionalDate(completeNextDueDate);
      if (!parsed) {
        setFormError('Use next due date YYYY-MM-DD');
        return;
      }
      payload.next_due_at = parsed;
    }
    await completeMaintenanceItem(membership.family_id, item.id, payload);
    setCompleteNextDueDate('');
    await reload();
  }

  async function submitAutoComplete(item: MaintenanceItemDto) {
    const mileage = Number(completeMileage);
    if (!Number.isFinite(mileage)) {
      setFormError('Enter a valid odometer reading');
      return;
    }
    setFormError(null);
    const payload: Record<string, unknown> = {
      completed_at: new Date().toISOString(),
      mileage_at_completion: mileage,
    };
    if (item.mileage_at_last_service != null) {
      payload.previous_service_mileage = item.mileage_at_last_service;
    }
    if (completeNextDueDate.trim()) {
      const parsed = parseOptionalDate(completeNextDueDate);
      if (parsed) {
        payload.next_due_at = parsed;
      }
    }
    await completeMaintenanceItem(membership.family_id, item.id, payload);
    setCompleteItemId(null);
    setCompleteMileage('');
    setCompleteNextDueDate('');
    await reload();
  }

  async function onStockChange(item: MaintenanceItemDto, status: StockStatus) {
    // Push local grocery lists first so the server can mirror onto every list.
    await runSync(membership.family_id);
    await setMaintenanceStockStatus(membership.family_id, item.id, status);
    await runSync(membership.family_id);
    await reload();
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <Text>Loading maintenance…</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Button title="Back" onPress={onBack} />
        <Text style={styles.title}>Maintenance</Text>
      </View>
      <View style={styles.tabRow}>
        {(['home', 'auto', 'items'] as MaintenanceCategory[]).map(option => (
          <Pressable
            key={option}
            style={[styles.tab, tab === option && styles.tabActive]}
            onPress={() => setTab(option)}>
            <Text style={styles.tabText}>
              {option === 'home' ? 'Home' : option === 'auto' ? 'Auto' : 'Items'}
            </Text>
          </Pressable>
        ))}
      </View>

      <Text style={styles.section}>
        {tab === 'items' ? 'Add household item' : `Add ${tab} maintenance`}
      </Text>
      <TextInput style={styles.input} placeholder="Title" value={title} onChangeText={setTitle} />
      {tab !== 'items' ? (
        <>
          <Text style={styles.label}>Type</Text>
          <View style={styles.chipRow}>
            {kinds.map(kind => (
              <Pressable
                key={kind}
                style={[styles.chip, itemKind === kind && styles.chipActive]}
                onPress={() => setItemKind(kind)}>
                <Text style={styles.chipText}>{KIND_LABELS[kind]}</Text>
              </Pressable>
            ))}
          </View>
          {tab === 'auto' ? (
            <TextInput
              style={styles.input}
              placeholder="Interval miles (optional)"
              value={intervalMiles}
              onChangeText={setIntervalMiles}
              keyboardType="number-pad"
            />
          ) : null}
          <TextInput
            style={styles.input}
            placeholder="Due by date (YYYY-MM-DD)"
            value={nextDueDate}
            onChangeText={setNextDueDate}
            autoCapitalize="none"
          />
        </>
      ) : null}
      {formError ? <Text style={styles.error}>{formError}</Text> : null}
      <Button title="Add item" onPress={() => onAdd().catch(() => undefined)} />

      <Text style={styles.section}>Active items</Text>
      {items.length === 0 ? <Text style={styles.muted}>No items yet.</Text> : null}
      {items.map(item => (
        <View key={item.id} style={styles.card}>
          <Text style={styles.cardTitle}>
            {item.title}
            {tab !== 'items' ? ` · ${KIND_LABELS[item.item_kind]}` : ''}
          </Text>
          {tab === 'items' ? (
            <>
              <Text style={styles.cardMeta}>
                Stock: {item.stock_status ? STOCK_LABELS[item.stock_status] : 'In stock'}
              </Text>
              <View style={styles.stockRow}>
                {(['in_stock', 'low', 'out'] as StockStatus[]).map(status => (
                  <Pressable
                    key={status}
                    style={[styles.chip, item.stock_status === status && styles.chipActive]}
                    onPress={() => onStockChange(item, status).catch(() => undefined)}>
                    <Text style={styles.chipText}>{STOCK_LABELS[status]}</Text>
                  </Pressable>
                ))}
              </View>
              <Text style={styles.cardMeta}>
                Low adds this item to every grocery list; Out shows it in red on lists.
              </Text>
            </>
          ) : (
            <>
              <Text style={styles.cardMeta}>
                {item.next_due_at
                  ? `Due ${formatReminderDateTime(item.next_due_at)}`
                  : 'No due date set'}
                {item.next_due_mileage != null ? ` · ${item.next_due_mileage.toLocaleString()} mi` : ''}
                {item.overdue ? ' · OVERDUE' : ''}
              </Text>
              {item.last_completed_at ? (
                <Text style={styles.cardMeta}>
                  Last done {formatReminderDateTime(item.last_completed_at)}
                </Text>
              ) : null}
              {completeItemId === item.id ? (
                <View style={styles.completeBox}>
                  <TextInput
                    style={styles.input}
                    placeholder="Odometer"
                    value={completeMileage}
                    onChangeText={setCompleteMileage}
                    keyboardType="number-pad"
                  />
                  <TextInput
                    style={styles.input}
                    placeholder="Next due (YYYY-MM-DD)"
                    value={completeNextDueDate}
                    onChangeText={setCompleteNextDueDate}
                    autoCapitalize="none"
                  />
                  <View style={styles.cardActions}>
                    <Button title="Save" onPress={() => submitAutoComplete(item).catch(() => undefined)} />
                    <Button title="Cancel" onPress={() => setCompleteItemId(null)} />
                  </View>
                </View>
              ) : (
                <View style={styles.completeBox}>
                  {item.category === 'home' ? (
                    <TextInput
                      style={styles.input}
                      placeholder="Next due after complete (YYYY-MM-DD)"
                      value={completeNextDueDate}
                      onChangeText={setCompleteNextDueDate}
                      autoCapitalize="none"
                    />
                  ) : null}
                  <View style={styles.cardActions}>
                    <Button title="Complete" onPress={() => onComplete(item).catch(() => undefined)} />
                    <Button
                      title="Delete"
                      onPress={() =>
                        deleteMaintenanceItem(membership.family_id, item.id)
                          .then(reload)
                          .catch(() => undefined)
                      }
                    />
                  </View>
                </View>
              )}
            </>
          )}
          {tab === 'items' ? (
            <Button
              title="Delete"
              onPress={() =>
                deleteMaintenanceItem(membership.family_id, item.id)
                  .then(reload)
                  .catch(() => undefined)
              }
            />
          ) : null}
        </View>
      ))}

      <Text style={styles.section}>History ({historyCount} records)</Text>
      <Text style={styles.muted}>Completed services are stored on the server for your records.</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16, paddingTop: 48, paddingBottom: 32 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  title: { fontSize: 22, fontWeight: '600', flex: 1 },
  tabRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  tab: { flex: 1, padding: 10, borderRadius: 8, backgroundColor: '#eee', alignItems: 'center' },
  tabActive: { backgroundColor: '#cde' },
  tabText: { fontWeight: '600' },
  section: { fontSize: 16, fontWeight: '600', marginTop: 16, marginBottom: 8 },
  label: { fontSize: 14, marginBottom: 4 },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
  },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  chip: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 16, backgroundColor: '#eee' },
  chipActive: { backgroundColor: '#cde' },
  chipText: { fontSize: 12 },
  error: { color: '#b00020', marginBottom: 8 },
  card: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#f7f7f7',
    marginBottom: 8,
  },
  cardTitle: { fontSize: 16, fontWeight: '500' },
  cardMeta: { fontSize: 12, color: '#555', marginTop: 4 },
  cardActions: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 },
  completeBox: { marginTop: 8 },
  stockRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  muted: { color: '#777', fontStyle: 'italic' },
});
