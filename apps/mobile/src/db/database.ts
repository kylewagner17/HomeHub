/** Singleton SQLite handle with versioned migrations (M3). */
import { open } from '@op-engineering/op-sqlite';

import { migrateLegacyEntityIds } from './migrateLegacyEntityIds';
import {
  CREATE_TABLES_V1,
  MIGRATE_V1_TO_V2,
  MIGRATE_V2_TO_V3,
  MIGRATE_V3_TO_V4,
  SCHEMA_VERSION,
} from './schema';

let dbInstance: ReturnType<typeof open> | null = null;

function runStatements(db: ReturnType<typeof open>, sql: string): void {
  for (const statement of sql.split(';')) {
    const trimmed = statement.trim();
    if (trimmed) {
      db.executeSync(trimmed);
    }
  }
}

function applyMigrations(db: ReturnType<typeof open>): void {
  runStatements(db, CREATE_TABLES_V1);
  const versionResult = db.executeSync('SELECT version FROM schema_version LIMIT 1');
  let version = 0;
  if ((versionResult.rows?.length ?? 0) > 0) {
    version = Number((versionResult.rows?.[0] as Record<string, unknown>).version);
  }
  if (version < 2) {
    runStatements(db, MIGRATE_V1_TO_V2);
    if (version === 0) {
      db.executeSync('INSERT INTO schema_version (version) VALUES (?)', [2]);
    } else {
      db.executeSync('UPDATE schema_version SET version = ?', [2]);
    }
    version = 2;
  }
  if (version < 3) {
    runStatements(db, MIGRATE_V2_TO_V3);
    db.executeSync('UPDATE schema_version SET version = ?', [3]);
    version = 3;
  }
  if (version < 4) {
    runStatements(db, MIGRATE_V3_TO_V4);
    db.executeSync('UPDATE schema_version SET version = ?', [4]);
    version = 4;
  }
  if (version < 5) {
    migrateLegacyEntityIds(db);
    db.executeSync('UPDATE schema_version SET version = ?', [SCHEMA_VERSION]);
  }
}

export function getDatabase() {
  if (!dbInstance) {
    dbInstance = open({ name: 'homehub.db' });
    applyMigrations(dbInstance);
  }
  return dbInstance;
}
