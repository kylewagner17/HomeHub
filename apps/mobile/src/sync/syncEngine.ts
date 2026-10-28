import type { GroceryListDto } from '@homehub/shared';

import {
  enqueueOutbox,
  getLastPullSince,
  listOutbox,
  removeOutboxKeys,
  setLastPullSince,
  type OutboxMutation,
} from '../db/outboxStore';
import { getLocalGroceryList, upsertLocalGroceryList } from '../db/groceryListStore';
import { mergeServerList } from './mergeGroceryList';
import { syncPull, syncPush } from './syncApi';

export type SyncStatus = 'idle' | 'syncing' | 'error' | 'offline';

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
        if (result.entity) {
          applyServerGroceryList(result.entity);
        }
        if (result.status === 'conflict' && result.entity) {
          applyServerGroceryList(result.entity);
          clearedKeys.push(result.idempotency_key);
        }
      }
      removeOutboxKeys(clearedKeys);
    }

    const since = getLastPullSince(familyId);
    const pullResult = await syncPull(familyId, since);
    for (const list of pullResult.grocery_lists) {
      applyServerGroceryList(list);
    }
    setLastPullSince(familyId, pullResult.server_time);
    return { status: 'ok' };
  } catch {
    return { status: 'error', message: 'Sync failed — changes stay queued offline' };
  }
}

function applyServerGroceryList(server: GroceryListDto): void {
  const local = getLocalGroceryList(server.id);
  const merged = mergeServerList(local, server);
  upsertLocalGroceryList(merged);
}

export function queueGroceryListUpsert(
  familyId: string,
  listId: string,
  name: string,
  revision: number,
): OutboxMutation {
  const mutation: OutboxMutation = {
    idempotency_key: `${listId}-${revision}-${Date.now()}`,
    entity_type: 'grocery_list',
    operation: 'upsert',
    entity_id: listId,
    data: { name, revision },
  };
  const now = new Date().toISOString();
  upsertLocalGroceryList({
    id: listId,
    familyId,
    name,
    revision,
    updatedAt: now,
    deleted: false,
  });
  enqueueOutbox(familyId, mutation);
  return mutation;
}

export function createLocalGroceryList(familyId: string, name: string): string {
  const listId = `list-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  queueGroceryListUpsert(familyId, listId, name.trim(), 1);
  return listId;
}
