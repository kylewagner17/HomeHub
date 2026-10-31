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
  maintenance_item_id: string | null;
  urgent_out: boolean;
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

export type ReminderRecurrence = 'one_time' | 'daily' | 'weekly' | 'monthly';

export type ReminderDto = {
  id: string;
  family_id: string;
  title: string;
  body: string | null;
  assignee_user_id: string | null;
  recurrence: ReminderRecurrence;
  enabled: boolean;
  next_fire_at: string;
  created_by: string | null;
  created_at: string;
  updated_at: string;
};

export type ReminderFireLogDto = {
  id: string;
  reminder_id: string;
  family_id: string;
  scheduled_at: string;
  fired_at: string;
  title: string;
};

export type UserNotificationDto = {
  id: string;
  family_id: string;
  reminder_id: string | null;
  title: string;
  body: string | null;
  created_at: string;
  read_at: string | null;
};

export type MaintenanceCategory = 'home' | 'auto' | 'items';

export type StockStatus = 'in_stock' | 'low' | 'out';

export type MaintenanceItemKind =
  | 'hvac_filter'
  | 'water_filter'
  | 'smoke_detector'
  | 'generic_home'
  | 'oil_change'
  | 'tire_rotation'
  | 'generic_auto'
  | 'consumable';

export type MaintenanceItemDto = {
  id: string;
  family_id: string;
  category: MaintenanceCategory;
  item_kind: MaintenanceItemKind;
  title: string;
  notes: string | null;
  last_completed_at: string | null;
  next_due_at: string | null;
  interval_days: number | null;
  interval_miles: number | null;
  mileage_at_last_service: number | null;
  previous_service_mileage: number | null;
  next_due_mileage: number | null;
  current_mileage: number | null;
  reminder_id: string | null;
  stock_status: StockStatus | null;
  overdue: boolean;
  created_at: string;
  updated_at: string;
};

export type MaintenanceCompletionDto = {
  id: string;
  item_id: string;
  family_id: string;
  completed_at: string;
  mileage_at_completion: number | null;
  previous_service_mileage: number | null;
  next_due_at: string | null;
  next_due_mileage: number | null;
  notes: string | null;
  created_at: string;
};
