/** Authenticated sync API calls (Bearer token from Keychain). */
import type { SyncPingResponseDto, SyncPullResponseDto, SyncPushResponseDto } from '@homehub/shared';

import { API_BASE_URL } from '../config/api';
import { getAccessToken } from './tokenStorage';
import type { OutboxMutation } from '../db/outboxStore';

async function authFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getAccessToken();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers as object),
      Authorization: `Bearer ${token ?? ''}`,
    },
  });
  if (!response.ok) {
    throw new Error(`Sync request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function syncPing(): Promise<SyncPingResponseDto> {
  return authFetch('/api/v1/sync/ping');
}

export async function syncPush(
  familyId: string,
  mutations: OutboxMutation[],
): Promise<SyncPushResponseDto> {
  return authFetch('/api/v1/sync/push', {
    method: 'POST',
    body: JSON.stringify({ family_id: familyId, mutations }),
  });
}

export async function syncPull(familyId: string, since: string | null): Promise<SyncPullResponseDto> {
  const params = new URLSearchParams({ family_id: familyId });
  if (since) {
    params.set('since', since);
  }
  return authFetch(`/api/v1/sync/pull?${params.toString()}`);
}
