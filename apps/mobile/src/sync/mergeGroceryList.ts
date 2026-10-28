import type { GroceryListDto } from '@homehub/shared';

export type LocalGroceryList = {
  id: string;
  familyId: string;
  name: string;
  revision: number;
  updatedAt: string;
  deleted: boolean;
};

export function mergeServerList(local: LocalGroceryList | null, server: GroceryListDto): LocalGroceryList {
  const serverDeleted = server.deleted_at !== null;
  if (local === null) {
    return {
      id: server.id,
      familyId: server.family_id,
      name: server.name,
      revision: server.revision,
      updatedAt: server.updated_at,
      deleted: serverDeleted,
    };
  }
  if (server.revision >= local.revision) {
    return {
      id: server.id,
      familyId: server.family_id,
      name: server.name,
      revision: server.revision,
      updatedAt: server.updated_at,
      deleted: serverDeleted,
    };
  }
  return local;
}
