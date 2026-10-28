import type { ApiErrorResponse, TokenResponse, UserResponse } from '@homehub/shared';

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
