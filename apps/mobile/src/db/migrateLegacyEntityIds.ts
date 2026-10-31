/**
 * Remap pre-UUID local ids (e.g. list-123-abc) so sync push passes API validation.
 * Runs once when upgrading schema to v5.
 */
import type { DB } from '@op-engineering/op-sqlite';

import type { OutboxMutation } from './outboxStore';
import { isEntityIdUuid, newEntityId } from '../sync/entityId';

type OutboxRow = {
  idempotency_key: string;
  family_id: string;
  payload: string;
  created_at: string;
};

function collectNonUuidIds(db: DB, table: string, column = 'id'): string[] {
  const result = db.executeSync(`SELECT ${column} AS v FROM ${table} WHERE ${column} IS NOT NULL`);
  const ids: string[] = [];
  for (const row of result.rows ?? []) {
    const v = String((row as Record<string, unknown>).v);
    if (v && !isEntityIdUuid(v)) {
      ids.push(v);
    }
  }
  return ids;
}

function buildIdMap(db: DB): Map<string, string> {
  const map = new Map<string, string>();
  const columns: Array<[string, string]> = [
    ['grocery_lists', 'id'],
    ['grocery_list_items', 'id'],
    ['grocery_list_items', 'list_id'],
    ['grocery_stores', 'id'],
    ['grocery_staples', 'id'],
    ['grocery_store_prices', 'id'],
    ['grocery_store_prices', 'store_id'],
    ['grocery_lists', 'selected_store_id'],
  ];
  for (const [table, column] of columns) {
    for (const oldId of collectNonUuidIds(db, table, column)) {
      if (!map.has(oldId)) {
        map.set(oldId, newEntityId());
      }
    }
  }
  return map;
}

function remapIdsInMutation(mutation: OutboxMutation, map: Map<string, string>): OutboxMutation {
  const replace = (id: string) => map.get(id) ?? id;
  const next: OutboxMutation = {
    ...mutation,
    entity_id: replace(mutation.entity_id),
    data: mutation.data ? { ...mutation.data } : null,
  };
  if (next.data) {
    if (typeof next.data.list_id === 'string') {
      next.data.list_id = replace(next.data.list_id);
    }
    if (typeof next.data.store_id === 'string') {
      next.data.store_id = replace(next.data.store_id);
    }
    if (typeof next.data.selected_store_id === 'string') {
      next.data.selected_store_id = replace(next.data.selected_store_id);
    }
  }
  return next;
}

function remapIdempotencyKey(key: string, map: Map<string, string>): string {
  let next = key;
  for (const [oldId, newId] of map) {
    if (next.includes(oldId)) {
      next = next.replaceAll(oldId, newId);
    }
  }
  return next;
}

export function migrateLegacyEntityIds(db: DB): void {
  const map = buildIdMap(db);
  if (map.size === 0) {
    return;
  }

  for (const [oldId, newId] of map) {
    db.executeSync('UPDATE grocery_lists SET id = ? WHERE id = ?', [newId, oldId]);
    db.executeSync('UPDATE grocery_list_items SET id = ? WHERE id = ?', [newId, oldId]);
    db.executeSync('UPDATE grocery_stores SET id = ? WHERE id = ?', [newId, oldId]);
    db.executeSync('UPDATE grocery_staples SET id = ? WHERE id = ?', [newId, oldId]);
    db.executeSync('UPDATE grocery_store_prices SET id = ? WHERE id = ?', [newId, oldId]);
  }
  for (const [oldId, newId] of map) {
    db.executeSync('UPDATE grocery_list_items SET list_id = ? WHERE list_id = ?', [newId, oldId]);
    db.executeSync('UPDATE grocery_store_prices SET store_id = ? WHERE store_id = ?', [
      newId,
      oldId,
    ]);
    db.executeSync('UPDATE grocery_lists SET selected_store_id = ? WHERE selected_store_id = ?', [
      newId,
      oldId,
    ]);
  }

  const outboxResult = db.executeSync(
    'SELECT idempotency_key, family_id, payload, created_at FROM sync_outbox',
  );
  const rows = (outboxResult.rows ?? []) as OutboxRow[];
  if (rows.length === 0) {
    return;
  }
  db.executeSync('DELETE FROM sync_outbox');
  for (const row of rows) {
    const mutation = remapIdsInMutation(JSON.parse(row.payload) as OutboxMutation, map);
    const idempotencyKey = remapIdempotencyKey(row.idempotency_key, map);
    db.executeSync(
      `INSERT INTO sync_outbox (idempotency_key, family_id, payload, created_at)
       VALUES (?, ?, ?, ?)`,
      [idempotencyKey, row.family_id, JSON.stringify(mutation), row.created_at],
    );
  }
}
