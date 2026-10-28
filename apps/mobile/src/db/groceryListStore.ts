import type { LocalGroceryList } from '../sync/mergeGroceryList';
import { getDatabase } from './database';

function rowToLocal(row: Record<string, unknown>): LocalGroceryList {
  return {
    id: String(row.id),
    familyId: String(row.family_id),
    name: String(row.name),
    selectedStoreId: row.selected_store_id ? String(row.selected_store_id) : null,
    revision: Number(row.revision),
    updatedAt: String(row.updated_at),
    deleted: Number(row.deleted) === 1,
  };
}

export function listLocalGroceryLists(familyId: string): LocalGroceryList[] {
  const db = getDatabase();
  const result = db.executeSync(
    'SELECT * FROM grocery_lists WHERE family_id = ? AND deleted = 0 ORDER BY name ASC',
    [familyId],
  );
  return (result.rows ?? []).map(row => rowToLocal(row as Record<string, unknown>));
}

export function upsertLocalGroceryList(list: LocalGroceryList): void {
  const db = getDatabase();
  db.execute(
    `INSERT INTO grocery_lists (id, family_id, name, selected_store_id, revision, updated_at, deleted)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       name = excluded.name,
       selected_store_id = excluded.selected_store_id,
       revision = excluded.revision,
       updated_at = excluded.updated_at,
       deleted = excluded.deleted`,
    [
      list.id,
      list.familyId,
      list.name,
      list.selectedStoreId,
      list.revision,
      list.updatedAt,
      list.deleted ? 1 : 0,
    ],
  );
}

export function getLocalGroceryList(id: string): LocalGroceryList | null {
  const db = getDatabase();
  const result = db.executeSync('SELECT * FROM grocery_lists WHERE id = ?', [id]);
  const row = result.rows?.[0] as Record<string, unknown> | undefined;
  return row ? rowToLocal(row) : null;
}
