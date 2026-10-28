import { open } from '@op-engineering/op-sqlite';

import { CREATE_TABLES_SQL, SCHEMA_VERSION } from './schema';

let dbInstance: ReturnType<typeof open> | null = null;

export function getDatabase() {
  if (!dbInstance) {
    dbInstance = open({ name: 'homehub.db' });
    for (const statement of CREATE_TABLES_SQL.split(';')) {
      const sql = statement.trim();
      if (sql) {
        dbInstance.executeSync(sql);
      }
    }
    const version = dbInstance.executeSync('SELECT version FROM schema_version LIMIT 1');
    if ((version.rows?.length ?? 0) === 0) {
      dbInstance.executeSync('INSERT INTO schema_version (version) VALUES (?)', [SCHEMA_VERSION]);
    }
  }
  return dbInstance;
}
