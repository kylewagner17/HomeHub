import type { SyncEntityType } from '@homehub/shared';

import { getDatabase } from './database';

/** Pending mutations uploaded via POST /api/v1/sync/push (one row per idempotency_key). */
export type OutboxMutation = {
  idempotency_key: string;
  entity_type: SyncEntityType;
  operation: 'upsert' | 'delete';
  entity_id: string;
  data: Record<string, unknown> | null;
};

export function enqueueOutbox(familyId: string, mutation: OutboxMutation): void {
  const db = getDatabase();
  const now = new Date().toISOString();
  db.executeSync(
    `INSERT OR REPLACE INTO sync_outbox (idempotency_key, family_id, payload, created_at)
     VALUES (?, ?, ?, ?)`,
    [mutation.idempotency_key, familyId, JSON.stringify(mutation), now],
  );
}

export function listOutbox(familyId: string): OutboxMutation[] {
  const db = getDatabase();
  const result = db.executeSync(
    'SELECT payload FROM sync_outbox WHERE family_id = ? ORDER BY id ASC',
    [familyId],
  );
  return (result.rows ?? []).map(row =>
    JSON.parse(String((row as Record<string, unknown>).payload)) as OutboxMutation,
  );
}

export function removeOutboxKeys(keys: string[]): void {
  if (keys.length === 0) {
    return;
  }
  const db = getDatabase();
  for (const key of keys) {
    db.executeSync('DELETE FROM sync_outbox WHERE idempotency_key = ?', [key]);
  }
}

export function getLastPullSince(familyId: string): string | null {
  const db = getDatabase();
  const result = db.executeSync('SELECT last_pull_since FROM sync_state WHERE family_id = ?', [
    familyId,
  ]);
  const row = result.rows?.[0] as Record<string, unknown> | undefined;
  return row?.last_pull_since ? String(row.last_pull_since) : null;
}

export function setLastPullSince(familyId: string, since: string): void {
  const db = getDatabase();
  db.executeSync(
    `INSERT INTO sync_state (family_id, last_pull_since) VALUES (?, ?)
     ON CONFLICT(family_id) DO UPDATE SET last_pull_since = excluded.last_pull_since`,
    [familyId, since],
  );
}
