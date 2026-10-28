/**
 * M3 list detail: view mode (shop/check off) vs edit mode (stores, prices, items).
 */
import type { FamilyMembershipSummary } from '@homehub/shared';
import React, { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Button,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import {
  listLocalItemsForList,
  listLocalPricesForStore,
  listLocalStores,
} from '../../db/groceryEntityStore';
import { getLocalGroceryList } from '../../db/groceryListStore';
import { getDatabase } from '../../db/database';
import {
  buildUnitPriceMap,
  estimateCartTotalCents,
  formatMoney,
  unitPriceCentsForItem,
} from './estimateCart';
import {
  addLocalListItem,
  afterListItemsChanged,
  changeListItemQuantity,
  createLocalStore,
  queueListSelectedStore,
  removeLocalGroceryList,
  removeLocalListItem,
  removeLocalStore,
  runSync,
  setLocalStorePrice,
  toggleLocalListItem,
} from '../../sync/syncEngine';
import { useRealtimeSync } from '../../sync/useRealtimeSync';

type Props = {
  membership: FamilyMembershipSummary;
  listId: string;
  onBack: () => void;
};

function ItemUnitPriceField({
  familyId,
  storeId,
  itemName,
  unitCents,
  onSaved,
}: {
  familyId: string;
  storeId: string;
  itemName: string;
  unitCents: number;
  onSaved: () => void;
}) {
  const [text, setText] = useState(() => (unitCents / 100).toFixed(2));

  useEffect(() => {
    setText((unitCents / 100).toFixed(2));
  }, [unitCents, itemName, storeId]);

  const commit = () => {
    const parsed = Number.parseFloat(text);
    const cents = Number.isFinite(parsed) ? Math.max(0, Math.round(parsed * 100)) : 0;
    setLocalStorePrice(familyId, storeId, itemName, cents);
    onSaved();
  };

  return (
    <TextInput
      style={styles.priceInput}
      value={text}
      onChangeText={setText}
      onEndEditing={commit}
      keyboardType="decimal-pad"
      placeholder="0.00"
    />
  );
}

export function GroceryListDetailScreen({ membership, listId, onBack }: Props) {
  const [tick, setTick] = useState(0);
  const [editing, setEditing] = useState(false);
  const refresh = useCallback(() => setTick(v => v + 1), []);
  const [newItem, setNewItem] = useState('');
  const [newStore, setNewStore] = useState('');

  useRealtimeSync(membership.family_id, refresh);

  React.useEffect(() => {
    getDatabase();
    runSync(membership.family_id)
      .then(() => refresh())
      .catch(() => undefined);
  }, [membership.family_id, refresh]);

  const list = getLocalGroceryList(listId);
  const items = listLocalItemsForList(listId);
  const stores = listLocalStores(membership.family_id);
  const selectedStoreId = list?.selectedStoreId ?? stores[0]?.id ?? null;
  const selectedStore = stores.find(s => s.id === selectedStoreId);
  const prices = selectedStoreId ? listLocalPricesForStore(selectedStoreId) : [];
  const priceMap = buildUnitPriceMap(
    prices.map(p => ({ itemName: p.itemName, priceCents: p.priceCents, revision: p.revision })),
  );
  const estimate = estimateCartTotalCents(
    items.map(i => ({ name: i.name, quantity: i.quantity, checked: i.checked })),
    prices.map(p => ({ itemName: p.itemName, priceCents: p.priceCents, revision: p.revision })),
  );

  const syncAndRefresh = useCallback(async () => {
    refresh();
    await afterListItemsChanged(membership.family_id);
    refresh();
  }, [membership.family_id, refresh]);

  const handleAddItem = useCallback(async () => {
    if (!newItem.trim()) {
      return;
    }
    addLocalListItem(membership.family_id, listId, newItem.trim());
    setNewItem('');
    await syncAndRefresh();
  }, [membership.family_id, listId, newItem, syncAndRefresh]);

  const handleAddStore = useCallback(async () => {
    if (!newStore.trim()) {
      return;
    }
    const storeId = createLocalStore(membership.family_id, newStore.trim());
    setNewStore('');
    queueListSelectedStore(membership.family_id, listId, storeId);
    await syncAndRefresh();
  }, [membership.family_id, listId, newStore, syncAndRefresh]);

  const handleSelectStore = useCallback(
    async (storeId: string) => {
      queueListSelectedStore(membership.family_id, listId, storeId);
      await syncAndRefresh();
    },
    [membership.family_id, listId, syncAndRefresh],
  );

  const handleRemoveStore = useCallback(
    (storeId: string, storeName: string) => {
      Alert.alert('Remove store?', `Remove "${storeName}" from this family?`, [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => {
            removeLocalStore(membership.family_id, storeId);
            syncAndRefresh().catch(() => undefined);
          },
        },
      ]);
    },
    [membership.family_id, syncAndRefresh],
  );

  const handleRemoveItem = useCallback(
    (itemId: string, itemName: string) => {
      Alert.alert('Remove item?', `Remove "${itemName}" from the list?`, [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => {
            removeLocalListItem(membership.family_id, itemId);
            syncAndRefresh().catch(() => undefined);
          },
        },
      ]);
    },
    [membership.family_id, syncAndRefresh],
  );

  const handleDeleteList = useCallback(() => {
    Alert.alert('Delete list?', `Delete "${list?.name}"? This cannot be undone.`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: () => {
          removeLocalGroceryList(membership.family_id, listId);
          afterListItemsChanged(membership.family_id)
            .then(() => onBack())
            .catch(() => onBack());
        },
      },
    ]);
  }, [list?.name, listId, membership.family_id, onBack]);

  const handleCheckOff = useCallback(
    (itemId: string) => {
      toggleLocalListItem(membership.family_id, itemId);
      syncAndRefresh().catch(() => undefined);
    },
    [membership.family_id, syncAndRefresh],
  );

  if (!list) {
    return (
      <View style={styles.container}>
        <Button title="Back" onPress={onBack} />
        <Text>List not found — sync or go back</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <View style={styles.headerSide}>
          <Button title="Back" onPress={onBack} />
        </View>
        <Text style={styles.title} numberOfLines={1}>
          {list.name}
        </Text>
        <View style={styles.headerSide}>
          <Pressable
            accessibilityRole="button"
            onPress={() => setEditing(value => !value)}
            style={styles.editButton}
          >
            <Text style={styles.editButtonText}>{editing ? 'Done' : 'Edit'}</Text>
          </Pressable>
        </View>
      </View>

      {editing ? (
        <Text style={styles.subtitle}>Add stores and items · set unit price on each line</Text>
      ) : null}

      {editing ? (
        <>
          <Text style={styles.section}>Store</Text>
          <View style={styles.rowWrap}>
            {stores.map(store => (
              <View key={store.id} style={styles.chipRow}>
                <Pressable
                  style={[styles.chip, selectedStoreId === store.id && styles.chipActive]}
                  onPress={() => handleSelectStore(store.id)}
                >
                  <Text>{store.name}</Text>
                </Pressable>
                <Pressable
                  style={styles.chipRemove}
                  onPress={() => handleRemoveStore(store.id, store.name)}
                  accessibilityLabel={`Remove ${store.name}`}
                >
                  <Text style={styles.chipRemoveText}>×</Text>
                </Pressable>
              </View>
            ))}
          </View>
          <View style={styles.row}>
            <TextInput
              style={styles.input}
              placeholder="Add store name"
              value={newStore}
              onChangeText={setNewStore}
            />
            <Button title="Add store" onPress={handleAddStore} />
          </View>
        </>
      ) : (
        <>
          <Text style={styles.section}>Store</Text>
          <Text style={styles.storeLabel}>
            {selectedStore?.name ?? 'No store selected — tap Edit to choose one'}
          </Text>
        </>
      )}

      <Text style={styles.estimate}>Est. total: {formatMoney(estimate.totalCents)}</Text>

      <Text style={styles.section}>Items</Text>
      {editing ? (
        <View style={styles.row}>
          <TextInput
            style={styles.input}
            placeholder="Item name"
            value={newItem}
            onChangeText={setNewItem}
          />
          <Button title="Add" onPress={handleAddItem} />
        </View>
      ) : null}
      <FlatList
        style={styles.itemsList}
        contentContainerStyle={styles.itemsListContent}
        data={items}
        extraData={`${tick}-${editing}`}
        keyExtractor={item => item.id}
        renderItem={({ item }) => {
          const unitCents = unitPriceCentsForItem(item.name, priceMap);
          const unitLabel = formatMoney(unitCents);

          const nameBlock = (
            <>
              <Text style={[styles.cardTitle, item.checked && styles.checked]}>
                {item.checked ? '✓ ' : ''}
                {item.name}
              </Text>
              {!editing ? (
                <Text style={styles.cardMeta}>
                  × {item.quantity} · {unitLabel} ea
                </Text>
              ) : null}
            </>
          );

          return (
            <View style={styles.card}>
              <View style={styles.itemRow}>
                <Pressable
                  style={styles.qtyButton}
                  onPress={() => {
                    changeListItemQuantity(membership.family_id, item.id, 1);
                    syncAndRefresh().catch(() => undefined);
                  }}
                >
                  <Text style={styles.qtyButtonText}>+</Text>
                </Pressable>
                <Text style={styles.qtyValue}>{item.quantity}</Text>
                <Pressable
                  style={styles.qtyButton}
                  onPress={() => {
                    changeListItemQuantity(membership.family_id, item.id, -1);
                    syncAndRefresh().catch(() => undefined);
                  }}
                >
                  <Text style={styles.qtyButtonText}>−</Text>
                </Pressable>
                {!editing ? (
                  <Pressable
                    style={styles.itemMain}
                    onPress={() => handleCheckOff(item.id)}
                    accessibilityRole="checkbox"
                    accessibilityState={{ checked: item.checked }}
                  >
                    {nameBlock}
                  </Pressable>
                ) : (
                  <View style={styles.itemMain}>
                    <Text style={[styles.cardTitle, item.checked && styles.checked]}>
                      {item.name}
                    </Text>
                    <View style={styles.editItemRow}>
                      {selectedStoreId ? (
                        <ItemUnitPriceField
                          familyId={membership.family_id}
                          storeId={selectedStoreId}
                          itemName={item.name}
                          unitCents={unitCents}
                          onSaved={() => {
                            syncAndRefresh().catch(() => undefined);
                          }}
                        />
                      ) : (
                        <Text style={styles.cardMeta}>Select a store to set prices</Text>
                      )}
                      <Pressable onPress={() => handleRemoveItem(item.id, item.name)}>
                        <Text style={styles.removeLink}>Remove</Text>
                      </Pressable>
                    </View>
                  </View>
                )}
              </View>
            </View>
          );
        }}
        ListEmptyComponent={
          <Text style={styles.empty}>
            {editing ? 'No items yet — add one above' : 'No items yet — tap Edit to add'}
          </Text>
        }
      />
      {editing ? (
        <View style={styles.bottomActions}>
          <Button title="Delete this list" color="#b00020" onPress={handleDeleteList} />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, paddingTop: 48, gap: 8 },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerSide: { minWidth: 72 },
  title: { flex: 1, fontSize: 20, fontWeight: '600', textAlign: 'center' },
  editButton: { alignSelf: 'flex-end', paddingVertical: 8, paddingHorizontal: 4 },
  editButtonText: { fontSize: 16, fontWeight: '600', color: '#0066cc' },
  subtitle: { color: '#555', marginBottom: 4, fontSize: 13 },
  section: { fontWeight: '600', marginTop: 8 },
  storeLabel: { fontSize: 16, color: '#222' },
  row: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  rowWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  itemsList: { flex: 1 },
  itemsListContent: { paddingBottom: 8 },
  bottomActions: { paddingTop: 8, paddingBottom: 8 },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 10,
  },
  priceInput: {
    width: 72,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 8,
    fontSize: 14,
  },
  chipRow: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#eee',
    borderRadius: 16,
  },
  chipActive: { backgroundColor: '#cde8ff' },
  chipRemove: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#fcc',
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipRemoveText: { fontSize: 18, fontWeight: '700', color: '#900' },
  estimate: { fontSize: 16, fontWeight: '500' },
  card: {
    padding: 12,
    backgroundColor: '#f4f4f4',
    borderRadius: 8,
    marginVertical: 4,
  },
  itemRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  qtyButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#ddd',
    alignItems: 'center',
    justifyContent: 'center',
  },
  qtyButtonText: { fontSize: 18, fontWeight: '600' },
  qtyValue: { minWidth: 24, textAlign: 'center', fontWeight: '600' },
  itemMain: { flex: 1 },
  editItemRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 6,
    flexWrap: 'wrap',
  },
  removeLink: { color: '#b00020', fontWeight: '600' },
  cardTitle: { fontSize: 16 },
  cardMeta: { fontSize: 13, color: '#555', marginTop: 2 },
  checked: { textDecorationLine: 'line-through', color: '#666' },
  empty: { textAlign: 'center', color: '#888', marginTop: 16 },
});
