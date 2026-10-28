import type { FamilyMembershipSummary } from '@homehub/shared';
import React, { useCallback, useState } from 'react';
import {
  Button,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { listLocalGroceryLists } from '../../db/groceryListStore';
import { getDatabase } from '../../db/database';
import { createLocalGroceryList, runSync } from '../../sync/syncEngine';

type Props = {
  membership: FamilyMembershipSummary;
  onBack: () => void;
};

export function GroceryListsScreen({ membership, onBack }: Props) {
  const [lists, setLists] = useState(() => listLocalGroceryLists(membership.family_id));
  const [newName, setNewName] = useState('');
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLists(listLocalGroceryLists(membership.family_id));
  }, [membership.family_id]);

  const handleSync = useCallback(async () => {
    setSyncMessage('Syncing…');
    const result = await runSync(membership.family_id);
    refresh();
    setSyncMessage(
      result.status === 'ok' ? 'Synced with server' : (result.message ?? 'Sync failed'),
    );
  }, [membership.family_id, refresh]);

  const handleAdd = useCallback(() => {
    if (!newName.trim()) {
      return;
    }
    createLocalGroceryList(membership.family_id, newName.trim());
    setNewName('');
    refresh();
    handleSync().catch(() => undefined);
  }, [membership.family_id, newName, refresh, handleSync]);

  React.useEffect(() => {
    getDatabase();
    handleSync().catch(() => undefined);
  }, [handleSync]);

  return (
    <View style={styles.container}>
      <Button title="Back" onPress={onBack} />
      <Text style={styles.title}>Grocery lists</Text>
      <Text style={styles.subtitle}>Offline-first · sync when online</Text>
      {syncMessage ? <Text style={styles.sync}>{syncMessage}</Text> : null}
      <View style={styles.row}>
        <TextInput
          style={styles.input}
          placeholder="New list name"
          value={newName}
          onChangeText={setNewName}
        />
        <Button title="Add" onPress={handleAdd} />
      </View>
      <FlatList
        data={lists}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>{item.name}</Text>
            <Text style={styles.cardMeta}>rev {item.revision}</Text>
          </View>
        )}
        ListEmptyComponent={<Text style={styles.empty}>No lists yet — add one above</Text>}
      />
      <Button title="Sync now" onPress={handleSync} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, paddingTop: 48, gap: 8 },
  title: { fontSize: 24, fontWeight: '600' },
  subtitle: { color: '#555', marginBottom: 8 },
  sync: { fontSize: 13, color: '#333' },
  row: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
  },
  card: {
    padding: 12,
    backgroundColor: '#f4f4f4',
    borderRadius: 8,
    marginVertical: 4,
  },
  cardTitle: { fontSize: 16, fontWeight: '500' },
  cardMeta: { fontSize: 12, color: '#666' },
  empty: { textAlign: 'center', color: '#888', marginTop: 24 },
});
