import type { GroceryListDto } from '@homehub/shared';

import { mergeByRevision, type RevisionEntity } from './mergeByRevision';

export type LocalGroceryList = RevisionEntity & {
  id: string;
  familyId: string;
  name: string;
  selectedStoreId: string | null;
};

export function mergeServerList(
  local: LocalGroceryList | null,
  server: GroceryListDto,
): LocalGroceryList {
  const serverLocal: LocalGroceryList = {
    id: server.id,
    familyId: server.family_id,
    name: server.name,
    selectedStoreId: server.selected_store_id,
    revision: server.revision,
    updatedAt: server.updated_at,
    deleted: server.deleted_at !== null,
  };
  return mergeByRevision(local, serverLocal);
}
