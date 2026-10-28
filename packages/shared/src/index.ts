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
  revision: number;
  updated_at: string;
  deleted_at: string | null;
};

export type SyncPushResultDto = {
  idempotency_key: string;
  status: string;
  entity: GroceryListDto | null;
};

export type SyncPushResponseDto = {
  results: SyncPushResultDto[];
};

export type SyncPullResponseDto = {
  server_time: string;
  grocery_lists: GroceryListDto[];
};

export type SyncPingResponseDto = {
  ok: boolean;
  server_time: string;
};
