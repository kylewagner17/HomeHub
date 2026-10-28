/** Revision-based merge for synced entities (ADR-003). */
export type RevisionEntity = {
  revision: number;
  updatedAt: string;
  deleted: boolean;
};

export function mergeByRevision<T extends RevisionEntity>(
  local: T | null,
  server: T,
): T {
  if (local === null) {
    return server;
  }
  if (server.revision >= local.revision) {
    return server;
  }
  return local;
}
