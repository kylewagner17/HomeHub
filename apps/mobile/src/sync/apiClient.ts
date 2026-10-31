/** HTTP client for auth and family onboarding (sync lives in syncApi.ts). */
import type {
  ApiErrorResponse,
  MaintenanceCategory,
  MaintenanceCompletionDto,
  MaintenanceItemDto,
  ReminderDto,
  ReminderFireLogDto,
  ReminderRecurrence,
  TokenResponse,
  UserNotificationDto,
  UserResponse,
} from '@homehub/shared';

import { API_BASE_URL } from '../config/api';
import { getAccessToken } from './tokenStorage';

export class ApiClientError extends Error {
  code: string;
  status: number;

  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };
  if (options.auth) {
    const token = await getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });
  if (!response.ok) {
    const body = (await response.json()) as ApiErrorResponse;
    throw new ApiClientError(
      body.error?.code ?? 'UNKNOWN',
      body.error?.message ?? response.statusText,
      response.status,
    );
  }
  return (await response.json()) as T;
}

export async function register(
  email: string,
  password: string,
  displayName: string,
): Promise<TokenResponse> {
  return request<TokenResponse>('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name: displayName }),
  });
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return request<TokenResponse>('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function fetchMe(): Promise<UserResponse> {
  return request<UserResponse>('/api/v1/auth/me', { auth: true });
}

export async function createFamily(name: string) {
  return request<{ id: string; name: string; invite_code: string }>('/api/v1/families', {
    method: 'POST',
    auth: true,
    body: JSON.stringify({ name }),
  });
}

export async function joinFamily(inviteCode: string) {
  return request<{ id: string; name: string; invite_code: string }>('/api/v1/families/join', {
    method: 'POST',
    auth: true,
    body: JSON.stringify({ invite_code: inviteCode }),
  });
}

export async function registerDeviceToken(platform: 'android' | 'ios', token: string): Promise<void> {
  await request<void>('/api/v1/auth/device-token', {
    method: 'PUT',
    auth: true,
    body: JSON.stringify({ platform, token }),
  });
}

export async function fetchReminders(familyId: string): Promise<ReminderDto[]> {
  return request<ReminderDto[]>(`/api/v1/families/${familyId}/reminders`, { auth: true });
}

export async function createReminder(
  familyId: string,
  payload: {
    title: string;
    body?: string;
    recurrence: ReminderRecurrence;
    next_fire_at: string;
  },
): Promise<ReminderDto> {
  return request<ReminderDto>(`/api/v1/families/${familyId}/reminders`, {
    method: 'POST',
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function deleteReminder(familyId: string, reminderId: string): Promise<void> {
  await request<void>(`/api/v1/families/${familyId}/reminders/${reminderId}`, {
    method: 'DELETE',
    auth: true,
  });
}

export async function fetchReminderHistory(familyId: string): Promise<ReminderFireLogDto[]> {
  return request<ReminderFireLogDto[]>(`/api/v1/families/${familyId}/reminders/history`, {
    auth: true,
  });
}

export async function fetchNotifications(since?: string): Promise<UserNotificationDto[]> {
  const query = since ? `?since=${encodeURIComponent(since)}` : '';
  return request<UserNotificationDto[]>(`/api/v1/notifications${query}`, { auth: true });
}

export async function markNotificationRead(notificationId: string): Promise<UserNotificationDto> {
  return request<UserNotificationDto>(`/api/v1/notifications/${notificationId}/read`, {
    method: 'PATCH',
    auth: true,
  });
}

export async function fetchMaintenanceItems(
  familyId: string,
  category: MaintenanceCategory,
): Promise<MaintenanceItemDto[]> {
  return request<MaintenanceItemDto[]>(
    `/api/v1/families/${familyId}/maintenance/items?category=${category}`,
    { auth: true },
  );
}

export async function createMaintenanceItem(
  familyId: string,
  payload: Record<string, unknown>,
): Promise<MaintenanceItemDto> {
  return request<MaintenanceItemDto>(`/api/v1/families/${familyId}/maintenance/items`, {
    method: 'POST',
    auth: true,
    body: JSON.stringify(payload),
  });
}

export async function completeMaintenanceItem(
  familyId: string,
  itemId: string,
  payload: Record<string, unknown>,
): Promise<MaintenanceItemDto> {
  return request<MaintenanceItemDto>(
    `/api/v1/families/${familyId}/maintenance/items/${itemId}/complete`,
    {
      method: 'POST',
      auth: true,
      body: JSON.stringify(payload),
    },
  );
}

export async function deleteMaintenanceItem(familyId: string, itemId: string): Promise<void> {
  await request<void>(`/api/v1/families/${familyId}/maintenance/items/${itemId}`, {
    method: 'DELETE',
    auth: true,
  });
}

export async function fetchMaintenanceHistory(familyId: string): Promise<MaintenanceCompletionDto[]> {
  return request<MaintenanceCompletionDto[]>(
    `/api/v1/families/${familyId}/maintenance/history`,
    { auth: true },
  );
}

export async function setMaintenanceStockStatus(
  familyId: string,
  itemId: string,
  stockStatus: import('@homehub/shared').StockStatus,
): Promise<MaintenanceItemDto> {
  return request<MaintenanceItemDto>(
    `/api/v1/families/${familyId}/maintenance/items/${itemId}/stock`,
    {
      method: 'PATCH',
      auth: true,
      body: JSON.stringify({ stock_status: stockStatus }),
    },
  );
}
