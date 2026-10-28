/** Local SQLite schema for offline groceries and sync metadata (M3). */
export const SCHEMA_VERSION = 3;

export const MIGRATE_V2_TO_V3 = `
ALTER TABLE grocery_stores ADD COLUMN external_provider TEXT;
ALTER TABLE grocery_stores ADD COLUMN external_store_id TEXT;
ALTER TABLE grocery_stores ADD COLUMN address_line TEXT;
`;

export const CREATE_TABLES_V1 = `
CREATE TABLE IF NOT EXISTS schema_version (
  version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS grocery_lists (
  id TEXT PRIMARY KEY NOT NULL,
  family_id TEXT NOT NULL,
  name TEXT NOT NULL,
  revision INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  deleted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sync_outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  idempotency_key TEXT NOT NULL UNIQUE,
  family_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_state (
  family_id TEXT PRIMARY KEY NOT NULL,
  last_pull_since TEXT
);
`;

export const MIGRATE_V1_TO_V2 = `
ALTER TABLE grocery_lists ADD COLUMN selected_store_id TEXT;

CREATE TABLE IF NOT EXISTS grocery_list_items (
  id TEXT PRIMARY KEY NOT NULL,
  list_id TEXT NOT NULL,
  family_id TEXT NOT NULL,
  name TEXT NOT NULL,
  quantity TEXT NOT NULL DEFAULT '1',
  checked INTEGER NOT NULL DEFAULT 0,
  staple_id TEXT,
  revision INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  deleted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS grocery_staples (
  id TEXT PRIMARY KEY NOT NULL,
  family_id TEXT NOT NULL,
  name TEXT NOT NULL,
  revision INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  deleted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS grocery_stores (
  id TEXT PRIMARY KEY NOT NULL,
  family_id TEXT NOT NULL,
  name TEXT NOT NULL,
  revision INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  deleted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS grocery_store_prices (
  id TEXT PRIMARY KEY NOT NULL,
  family_id TEXT NOT NULL,
  store_id TEXT NOT NULL,
  item_name TEXT NOT NULL,
  price_cents INTEGER NOT NULL,
  revision INTEGER NOT NULL,
  updated_at TEXT NOT NULL,
  deleted INTEGER NOT NULL DEFAULT 0
);
`;

export const CREATE_TABLES_SQL = CREATE_TABLES_V1;
