/**
 * Offline-first sync: push outbox mutations, then pull server changes.
 * Conflict merge rules live in merge* modules (ADR-003, ADR-004).
 */
import type {
  GroceryListDto,
  GroceryListItemDto,
  GroceryStapleDto,
  GroceryStoreDto,
  GroceryStorePriceDto,
  SyncPushResultDto,
} from '@homehub/shared';

import {
  getLocalListItem,
  getLocalStore,
  getLocalStorePrice,
  getLocalStaple,
  listLocalItemsForList,
  listLocalPricesForStore,
  upsertLocalListItem,
  upsertLocalStaple,
  upsertLocalStore,
  upsertLocalStorePrice,
} from '../db/groceryEntityStore';
import { getLocalGroceryList, listLocalGroceryLists, upsertLocalGroceryList } from '../db/groceryListStore';
import { addQuantities, adjustQuantity } from '../features/groceries/quantity';
import {
  enqueueOutbox,
  getLastPullSince,
  listOutbox,
  removeOutboxKeys,
  setLastPullSince,
  type OutboxMutation,
} from '../db/outboxStore';
import {
  mergeServerListItem,
  mergeServerStaple,
  mergeServerStore,
  mergeServerStorePrice,
} from './mergeGroceryEntities';
import { mergeServerList } from './mergeGroceryList';
import { syncPull, syncPush } from './syncApi';

function newId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function applyPushResult(result: SyncPushResultDto): void {
  if (result.entity) {
    applyServerGroceryList(result.entity);
  }
  if (result.grocery_list_item) {
    applyServerListItem(result.grocery_list_item);
  }
  if (result.grocery_staple) {
    applyServerStaple(result.grocery_staple);
  }
  if (result.grocery_store) {
    applyServerStore(result.grocery_store);
  }
  if (result.grocery_store_price) {
    applyServerStorePrice(result.grocery_store_price);
  }
}

export async function runSync(familyId: string): Promise<{ status: 'ok' | 'error'; message?: string }> {
  try {
    const outbox = listOutbox(familyId);
    const clearedKeys: string[] = [];

    if (outbox.length > 0) {
      const pushResult = await syncPush(familyId, outbox);
      for (const result of pushResult.results) {
        if (result.status === 'applied' || result.status === 'duplicate') {
          clearedKeys.push(result.idempotency_key);
        }
        applyPushResult(result);
        if (result.status === 'conflict') {
          clearedKeys.push(result.idempotency_key);
        }
      }
      removeOutboxKeys(clearedKeys);
    }

    const since = getLastPullSince(familyId);
    const pullResult = await syncPull(familyId, since);
    for (const list of pullResult.grocery_lists ?? []) {
      applyServerGroceryList(list);
    }
    for (const item of pullResult.grocery_list_items ?? []) {
      applyServerListItem(item);
    }
    for (const staple of pullResult.grocery_staples ?? []) {
      applyServerStaple(staple);
    }
    for (const store of pullResult.grocery_stores ?? []) {
      applyServerStore(store);
    }
    for (const price of pullResult.grocery_store_prices ?? []) {
      applyServerStorePrice(price);
    }
    setLastPullSince(familyId, pullResult.server_time);
    return { status: 'ok' };
  } catch {
    return { status: 'error', message: 'Sync failed — changes stay queued offline' };
  }
}

function applyServerGroceryList(server: GroceryListDto): void {
  const local = getLocalGroceryList(server.id);
  upsertLocalGroceryList(mergeServerList(local, server));
}

function applyServerListItem(server: GroceryListItemDto): void {
  const local = getLocalListItem(server.id);
  upsertLocalListItem(mergeServerListItem(local, server));
}

function applyServerStaple(server: GroceryStapleDto): void {
  const local = getLocalStaple(server.id);
  upsertLocalStaple(mergeServerStaple(local, server));
}

function applyServerStore(server: GroceryStoreDto): void {
  const local = getLocalStore(server.id);
  upsertLocalStore(mergeServerStore(local, server));
}

function applyServerStorePrice(server: GroceryStorePriceDto): void {
  const local = getLocalStorePrice(server.id);
  upsertLocalStorePrice(mergeServerStorePrice(local, server));
}

function queueMutation(familyId: string, mutation: OutboxMutation): void {
  enqueueOutbox(familyId, mutation);
}

export function queueGroceryListUpsert(
  familyId: string,
  listId: string,
  name: string,
  revision: number,
  selectedStoreId: string | null = null,
): OutboxMutation {
  const mutation: OutboxMutation = {
    idempotency_key: `${listId}-${revision}-${Date.now()}`,
    entity_type: 'grocery_list',
    operation: 'upsert',
    entity_id: listId,
    data: { name, revision, selected_store_id: selectedStoreId },
  };
  const now = new Date().toISOString();
  upsertLocalGroceryList({
    id: listId,
    familyId,
    name,
    selectedStoreId,
    revision,
    updatedAt: now,
    deleted: false,
  });
  queueMutation(familyId, mutation);
  return mutation;
}

export function createLocalGroceryList(familyId: string, name: string): string {
  const listId = newId('list');
  queueGroceryListUpsert(familyId, listId, name.trim(), 1);
  return listId;
}

export function queueListSelectedStore(
  familyId: string,
  listId: string,
  storeId: string | null,
): void {
  const local = getLocalGroceryList(listId);
  if (!local) {
    return;
  }
  const revision = local.revision + 1;
  queueGroceryListUpsert(familyId, listId, local.name, revision, storeId);
}

export function queueListItemUpsert(
  familyId: string,
  listId: string,
  itemId: string,
  name: string,
  quantity: string,
  checked: boolean,
  revision: number,
): OutboxMutation {
  const mutation: OutboxMutation = {
    idempotency_key: `${itemId}-${revision}-${Date.now()}`,
    entity_type: 'grocery_list_item',
    operation: 'upsert',
    entity_id: itemId,
    data: { name, list_id: listId, quantity, checked, revision },
  };
  const now = new Date().toISOString();
  upsertLocalListItem({
    id: itemId,
    listId,
    familyId,
    name,
    quantity,
    checked,
    stapleId: null,
    revision,
    updatedAt: now,
    deleted: false,
  });
  queueMutation(familyId, mutation);
  return mutation;
}

export function addLocalListItem(familyId: string, listId: string, name: string): string {
  const trimmed = name.trim();
  const existing = listLocalItemsForList(listId).find(
    item => item.name.toLowerCase() === trimmed.toLowerCase(),
  );
  if (existing) {
    const quantity = addQuantities(existing.quantity, '1');
    queueListItemUpsert(
      familyId,
      listId,
      existing.id,
      existing.name,
      quantity,
      existing.checked,
      existing.revision + 1,
    );
    return existing.id;
  }
  const itemId = newId('item');
  queueListItemUpsert(familyId, listId, itemId, trimmed, '1', false, 1);
  return itemId;
}

export function changeListItemQuantity(
  familyId: string,
  itemId: string,
  delta: number,
): void {
  const local = getLocalListItem(itemId);
  if (!local) {
    return;
  }
  const nextQuantity = adjustQuantity(local.quantity, delta);
  if (nextQuantity === null) {
    removeLocalListItem(familyId, itemId);
    return;
  }
  queueListItemUpsert(
    familyId,
    local.listId,
    itemId,
    local.name,
    nextQuantity,
    local.checked,
    local.revision + 1,
  );
}

export async function afterListItemsChanged(familyId: string): Promise<void> {
  await runSync(familyId);
}

export function setLocalStorePrice(
  familyId: string,
  storeId: string,
  itemName: string,
  priceCents: number,
): void {
  const existing = listLocalPricesForStore(storeId).find(
    p => p.itemName.toLowerCase() === itemName.trim().toLowerCase(),
  );
  const priceId = existing?.id ?? newId('price');
  const revision = (existing?.revision ?? 0) + 1;
  const mutation: OutboxMutation = {
    idempotency_key: `${priceId}-${revision}-${Date.now()}`,
    entity_type: 'grocery_store_price',
    operation: 'upsert',
    entity_id: priceId,
    data: {
      store_id: storeId,
      item_name: itemName.trim(),
      price_cents: priceCents,
      revision,
    },
  };
  const now = new Date().toISOString();
  upsertLocalStorePrice({
    id: priceId,
    familyId,
    storeId,
    itemName: itemName.trim(),
    priceCents,
    revision,
    updatedAt: now,
    deleted: false,
  });
  queueMutation(familyId, mutation);
}

export function removeLocalListItem(familyId: string, itemId: string): void {
  const local = getLocalListItem(itemId);
  if (!local) {
    return;
  }
  const revision = local.revision + 1;
  const now = new Date().toISOString();
  const mutation: OutboxMutation = {
    idempotency_key: `del-item-${itemId}-${Date.now()}`,
    entity_type: 'grocery_list_item',
    operation: 'delete',
    entity_id: itemId,
    data: { revision },
  };
  upsertLocalListItem({
    ...local,
    revision,
    updatedAt: now,
    deleted: true,
  });
  queueMutation(familyId, mutation);
}

export function removeLocalGroceryList(familyId: string, listId: string): void {
  const local = getLocalGroceryList(listId);
  if (!local) {
    return;
  }
  const revision = local.revision + 1;
  const now = new Date().toISOString();
  const mutation: OutboxMutation = {
    idempotency_key: `del-list-${listId}-${Date.now()}`,
    entity_type: 'grocery_list',
    operation: 'delete',
    entity_id: listId,
    data: { name: local.name, revision },
  };
  upsertLocalGroceryList({
    ...local,
    revision,
    updatedAt: now,
    deleted: true,
  });
  queueMutation(familyId, mutation);
}

export function removeLocalStore(familyId: string, storeId: string): void {
  const local = getLocalStore(storeId);
  if (!local) {
    return;
  }
  const revision = local.revision + 1;
  const now = new Date().toISOString();
  const mutation: OutboxMutation = {
    idempotency_key: `del-store-${storeId}-${Date.now()}`,
    entity_type: 'grocery_store',
    operation: 'delete',
    entity_id: storeId,
    data: { name: local.name, revision },
  };
  upsertLocalStore({
    ...local,
    revision,
    updatedAt: now,
    deleted: true,
  });
  queueMutation(familyId, mutation);
  for (const list of listLocalGroceryLists(familyId)) {
    if (list.selectedStoreId === storeId) {
      queueListSelectedStore(familyId, list.id, null);
    }
  }
}

export function toggleLocalListItem(familyId: string, itemId: string): void {
  const local = getLocalListItem(itemId);
  if (!local) {
    return;
  }
  const revision = local.revision + 1;
  queueListItemUpsert(
    familyId,
    local.listId,
    itemId,
    local.name,
    local.quantity,
    !local.checked,
    revision,
  );
}

export function createLocalStore(familyId: string, name: string): string {
  const storeId = newId('store');
  const mutation: OutboxMutation = {
    idempotency_key: `${storeId}-1-${Date.now()}`,
    entity_type: 'grocery_store',
    operation: 'upsert',
    entity_id: storeId,
    data: { name: name.trim(), revision: 1 },
  };
  const now = new Date().toISOString();
  upsertLocalStore({
    id: storeId,
    familyId,
    name: name.trim(),
    externalProvider: null,
    externalStoreId: null,
    addressLine: null,
    revision: 1,
    updatedAt: now,
    deleted: false,
  });
  queueMutation(familyId, mutation);
  return storeId;
}

export function createLocalStaple(familyId: string, name: string): string {
  const stapleId = newId('staple');
  const mutation: OutboxMutation = {
    idempotency_key: `${stapleId}-1-${Date.now()}`,
    entity_type: 'grocery_staple',
    operation: 'upsert',
    entity_id: stapleId,
    data: { name: name.trim(), revision: 1 },
  };
  const now = new Date().toISOString();
  upsertLocalStaple({
    id: stapleId,
    familyId,
    name: name.trim(),
    revision: 1,
    updatedAt: now,
    deleted: false,
  });
  queueMutation(familyId, mutation);
  return stapleId;
}
