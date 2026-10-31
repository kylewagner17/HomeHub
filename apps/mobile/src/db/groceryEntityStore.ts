import type {
  LocalGroceryListItem,
  LocalGroceryStaple,
  LocalGroceryStore,
  LocalGroceryStorePrice,
} from '../sync/mergeGroceryEntities';
import { getDatabase } from './database';

function itemFromRow(row: Record<string, unknown>): LocalGroceryListItem {
  return {
    id: String(row.id),
    listId: String(row.list_id),
    familyId: String(row.family_id),
    name: String(row.name),
    quantity: String(row.quantity),
    checked: Number(row.checked) === 1,
    stapleId: row.staple_id ? String(row.staple_id) : null,
    maintenanceItemId: row.maintenance_item_id ? String(row.maintenance_item_id) : null,
    urgentOut: Number(row.urgent_out ?? 0) === 1,
    revision: Number(row.revision),
    updatedAt: String(row.updated_at),
    deleted: Number(row.deleted) === 1,
  };
}

export function listLocalItemsForList(listId: string): LocalGroceryListItem[] {
  const db = getDatabase();
  const result = db.executeSync(
    'SELECT * FROM grocery_list_items WHERE list_id = ? AND deleted = 0 ORDER BY name ASC',
    [listId],
  );
  return (result.rows ?? []).map(row => itemFromRow(row as Record<string, unknown>));
}

export function getLocalListItem(id: string): LocalGroceryListItem | null {
  const db = getDatabase();
  const result = db.executeSync('SELECT * FROM grocery_list_items WHERE id = ?', [id]);
  const row = result.rows?.[0] as Record<string, unknown> | undefined;
  return row ? itemFromRow(row) : null;
}

export function upsertLocalListItem(item: LocalGroceryListItem): void {
  const db = getDatabase();
  db.execute(
    `INSERT INTO grocery_list_items
     (id, list_id, family_id, name, quantity, checked, staple_id, maintenance_item_id, urgent_out, revision, updated_at, deleted)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       list_id = excluded.list_id,
       name = excluded.name,
       quantity = excluded.quantity,
       checked = excluded.checked,
       staple_id = excluded.staple_id,
       maintenance_item_id = excluded.maintenance_item_id,
       urgent_out = excluded.urgent_out,
       revision = excluded.revision,
       updated_at = excluded.updated_at,
       deleted = excluded.deleted`,
    [
      item.id,
      item.listId,
      item.familyId,
      item.name,
      item.quantity,
      item.checked ? 1 : 0,
      item.stapleId,
      item.maintenanceItemId,
      item.urgentOut ? 1 : 0,
      item.revision,
      item.updatedAt,
      item.deleted ? 1 : 0,
    ],
  );
}

export function listLocalStores(familyId: string): LocalGroceryStore[] {
  const db = getDatabase();
  const result = db.executeSync(
    'SELECT * FROM grocery_stores WHERE family_id = ? AND deleted = 0 ORDER BY name ASC',
    [familyId],
  );
  return (result.rows ?? []).map(row => ({
    id: String(row.id),
    familyId: String(row.family_id),
    name: String(row.name),
    externalProvider: row.external_provider ? String(row.external_provider) : null,
    externalStoreId: row.external_store_id ? String(row.external_store_id) : null,
    addressLine: row.address_line ? String(row.address_line) : null,
    revision: Number(row.revision),
    updatedAt: String(row.updated_at),
    deleted: Number(row.deleted) === 1,
  }));
}

export function getLocalStore(id: string): LocalGroceryStore | null {
  const db = getDatabase();
  const result = db.executeSync('SELECT * FROM grocery_stores WHERE id = ?', [id]);
  const row = result.rows?.[0] as Record<string, unknown> | undefined;
  if (!row) {
    return null;
  }
  return {
    id: String(row.id),
    familyId: String(row.family_id),
    name: String(row.name),
    externalProvider: row.external_provider ? String(row.external_provider) : null,
    externalStoreId: row.external_store_id ? String(row.external_store_id) : null,
    addressLine: row.address_line ? String(row.address_line) : null,
    revision: Number(row.revision),
    updatedAt: String(row.updated_at),
    deleted: Number(row.deleted) === 1,
  };
}

export function upsertLocalStore(store: LocalGroceryStore): void {
  const db = getDatabase();
  db.execute(
    `INSERT INTO grocery_stores
     (id, family_id, name, external_provider, external_store_id, address_line, revision, updated_at, deleted)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       name = excluded.name,
       external_provider = excluded.external_provider,
       external_store_id = excluded.external_store_id,
       address_line = excluded.address_line,
       revision = excluded.revision,
       updated_at = excluded.updated_at,
       deleted = excluded.deleted`,
    [
      store.id,
      store.familyId,
      store.name,
      store.externalProvider,
      store.externalStoreId,
      store.addressLine,
      store.revision,
      store.updatedAt,
      store.deleted ? 1 : 0,
    ],
  );
}

export function listLocalStaples(familyId: string): LocalGroceryStaple[] {
  const db = getDatabase();
  const result = db.executeSync(
    'SELECT * FROM grocery_staples WHERE family_id = ? AND deleted = 0 ORDER BY name ASC',
    [familyId],
  );
  return (result.rows ?? []).map(row => ({
    id: String(row.id),
    familyId: String(row.family_id),
    name: String(row.name),
    revision: Number(row.revision),
    updatedAt: String(row.updated_at),
    deleted: Number(row.deleted) === 1,
  }));
}

export function upsertLocalStaple(staple: LocalGroceryStaple): void {
  const db = getDatabase();
  db.execute(
    `INSERT INTO grocery_staples (id, family_id, name, revision, updated_at, deleted)
     VALUES (?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       name = excluded.name,
       revision = excluded.revision,
       updated_at = excluded.updated_at,
       deleted = excluded.deleted`,
    [
      staple.id,
      staple.familyId,
      staple.name,
      staple.revision,
      staple.updatedAt,
      staple.deleted ? 1 : 0,
    ],
  );
}

export function listLocalPricesForStore(storeId: string): LocalGroceryStorePrice[] {
  const db = getDatabase();
  const result = db.executeSync(
    'SELECT * FROM grocery_store_prices WHERE store_id = ? AND deleted = 0',
    [storeId],
  );
  return (result.rows ?? []).map(row => ({
    id: String(row.id),
    familyId: String(row.family_id),
    storeId: String(row.store_id),
    itemName: String(row.item_name),
    priceCents: Number(row.price_cents),
    revision: Number(row.revision),
    updatedAt: String(row.updated_at),
    deleted: Number(row.deleted) === 1,
  }));
}

export function getLocalStorePrice(id: string): LocalGroceryStorePrice | null {
  const db = getDatabase();
  const result = db.executeSync('SELECT * FROM grocery_store_prices WHERE id = ?', [id]);
  const row = result.rows?.[0] as Record<string, unknown> | undefined;
  if (!row) {
    return null;
  }
  return {
    id: String(row.id),
    familyId: String(row.family_id),
    storeId: String(row.store_id),
    itemName: String(row.item_name),
    priceCents: Number(row.price_cents),
    revision: Number(row.revision),
    updatedAt: String(row.updated_at),
    deleted: Number(row.deleted) === 1,
  };
}

export function upsertLocalStorePrice(price: LocalGroceryStorePrice): void {
  const db = getDatabase();
  db.execute(
    `INSERT INTO grocery_store_prices
     (id, family_id, store_id, item_name, price_cents, revision, updated_at, deleted)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       store_id = excluded.store_id,
       item_name = excluded.item_name,
       price_cents = excluded.price_cents,
       revision = excluded.revision,
       updated_at = excluded.updated_at,
       deleted = excluded.deleted`,
    [
      price.id,
      price.familyId,
      price.storeId,
      price.itemName,
      price.priceCents,
      price.revision,
      price.updatedAt,
      price.deleted ? 1 : 0,
    ],
  );
}

export function getLocalStaple(id: string): LocalGroceryStaple | null {
  const db = getDatabase();
  const result = db.executeSync('SELECT * FROM grocery_staples WHERE id = ?', [id]);
  const row = result.rows?.[0] as Record<string, unknown> | undefined;
  if (!row) {
    return null;
  }
  return {
    id: String(row.id),
    familyId: String(row.family_id),
    name: String(row.name),
    revision: Number(row.revision),
    updatedAt: String(row.updated_at),
    deleted: Number(row.deleted) === 1,
  };
}
