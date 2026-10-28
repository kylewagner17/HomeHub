import type {
  GroceryListItemDto,
  GroceryStapleDto,
  GroceryStoreDto,
  GroceryStorePriceDto,
} from '@homehub/shared';

import { mergeByRevision, type RevisionEntity } from './mergeByRevision';

export type LocalGroceryListItem = RevisionEntity & {
  id: string;
  listId: string;
  familyId: string;
  name: string;
  quantity: string;
  checked: boolean;
  stapleId: string | null;
};

export type LocalGroceryStaple = RevisionEntity & {
  id: string;
  familyId: string;
  name: string;
};

export type LocalGroceryStore = RevisionEntity & {
  id: string;
  familyId: string;
  name: string;
  externalProvider: string | null;
  externalStoreId: string | null;
  addressLine: string | null;
};

export type LocalGroceryStorePrice = RevisionEntity & {
  id: string;
  familyId: string;
  storeId: string;
  itemName: string;
  priceCents: number;
};

export function mergeServerListItem(
  local: LocalGroceryListItem | null,
  server: GroceryListItemDto,
): LocalGroceryListItem {
  return mergeByRevision(local, dtoToLocalItem(server));
}

export function mergeServerStaple(
  local: LocalGroceryStaple | null,
  server: GroceryStapleDto,
): LocalGroceryStaple {
  return mergeByRevision(local, dtoToLocalStaple(server));
}

export function mergeServerStore(
  local: LocalGroceryStore | null,
  server: GroceryStoreDto,
): LocalGroceryStore {
  return mergeByRevision(local, dtoToLocalStore(server));
}

export function mergeServerStorePrice(
  local: LocalGroceryStorePrice | null,
  server: GroceryStorePriceDto,
): LocalGroceryStorePrice {
  return mergeByRevision(local, dtoToLocalPrice(server));
}

function dtoToLocalItem(server: GroceryListItemDto): LocalGroceryListItem {
  return {
    id: server.id,
    listId: server.list_id,
    familyId: server.family_id,
    name: server.name,
    quantity: server.quantity,
    checked: server.checked,
    stapleId: server.staple_id,
    revision: server.revision,
    updatedAt: server.updated_at,
    deleted: server.deleted_at !== null,
  };
}

function dtoToLocalStaple(server: GroceryStapleDto): LocalGroceryStaple {
  return {
    id: server.id,
    familyId: server.family_id,
    name: server.name,
    revision: server.revision,
    updatedAt: server.updated_at,
    deleted: server.deleted_at !== null,
  };
}

function dtoToLocalStore(server: GroceryStoreDto): LocalGroceryStore {
  return {
    id: server.id,
    familyId: server.family_id,
    name: server.name,
    externalProvider: server.external_provider,
    externalStoreId: server.external_store_id,
    addressLine: server.address_line,
    revision: server.revision,
    updatedAt: server.updated_at,
    deleted: server.deleted_at !== null,
  };
}

function dtoToLocalPrice(server: GroceryStorePriceDto): LocalGroceryStorePrice {
  return {
    id: server.id,
    familyId: server.family_id,
    storeId: server.store_id,
    itemName: server.item_name,
    priceCents: server.price_cents,
    revision: server.revision,
    updatedAt: server.updated_at,
    deleted: server.deleted_at !== null,
  };
}
