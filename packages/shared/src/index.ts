export type ApiErrorBody = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export type ApiErrorResponse = {
  error: ApiErrorBody;
};

export type HealthResponse = {
  status: string;
  database: string;
  version: string;
};

export type FamilyRole = 'admin' | 'member';

export type FamilyMembershipSummary = {
  family_id: string;
  family_name: string;
  role: FamilyRole;
  invite_code: string;
};

export type UserResponse = {
  id: string;
  email: string;
  display_name: string;
  memberships: FamilyMembershipSummary[];
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: UserResponse;
};

export type FamilyResponse = {
  id: string;
  name: string;
  invite_code: string;
};

export type GroceryListDto = {
  id: string;
  family_id: string;
  name: string;
  selected_store_id: string | null;
  revision: number;
  updated_at: string;
  deleted_at: string | null;
};

export type GroceryListItemDto = {
  id: string;
  list_id: string;
  family_id: string;
  name: string;
  quantity: string;
  checked: boolean;
  staple_id: string | null;
  revision: number;
  updated_at: string;
  deleted_at: string | null;
};

export type GroceryStapleDto = {
  id: string;
  family_id: string;
  name: string;
  revision: number;
  updated_at: string;
  deleted_at: string | null;
};

export type GroceryStoreDto = {
  id: string;
  family_id: string;
  name: string;
  external_provider: string | null;
  external_store_id: string | null;
  address_line: string | null;
  revision: number;
  updated_at: string;
  deleted_at: string | null;
};

export type GroceryStorePriceDto = {
  id: string;
  family_id: string;
  store_id: string;
  item_name: string;
  price_cents: number;
  revision: number;
  updated_at: string;
  deleted_at: string | null;
};

export type SyncEntityType =
  | 'grocery_list'
  | 'grocery_list_item'
  | 'grocery_staple'
  | 'grocery_store'
  | 'grocery_store_price';

export type SyncPushResultDto = {
  idempotency_key: string;
  status: string;
  entity_type?: SyncEntityType;
  entity: GroceryListDto | null;
  grocery_list_item?: GroceryListItemDto | null;
  grocery_staple?: GroceryStapleDto | null;
  grocery_store?: GroceryStoreDto | null;
  grocery_store_price?: GroceryStorePriceDto | null;
};

export type SyncPushResponseDto = {
  results: SyncPushResultDto[];
};

export type SyncPullResponseDto = {
  server_time: string;
  grocery_lists: GroceryListDto[];
  grocery_list_items: GroceryListItemDto[];
  grocery_staples: GroceryStapleDto[];
  grocery_stores: GroceryStoreDto[];
  grocery_store_prices: GroceryStorePriceDto[];
};

export type SyncPingResponseDto = {
  ok: boolean;
  server_time: string;
};
