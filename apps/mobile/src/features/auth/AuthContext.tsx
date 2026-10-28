import type { UserResponse } from '@homehub/shared';
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import * as api from '../../sync/apiClient';
import { clearAccessToken, saveAccessToken } from '../../sync/tokenStorage';

type AuthState = {
  user: UserResponse | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, displayName: string) => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    // On cold start, restore session from Keychain token if still valid.
    try {
      const me = await api.fetchMe();
      setUser(me);
    } catch {
      setUser(null);
      await clearAccessToken();
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        await refreshUser();
      } finally {
        setLoading(false);
      }
    })();
  }, [refreshUser]);

  const signIn = useCallback(async (email: string, password: string) => {
    const result = await api.login(email, password);
    await saveAccessToken(result.access_token);
    setUser(result.user);
  }, []);

  const signUp = useCallback(async (email: string, password: string, displayName: string) => {
    const result = await api.register(email, password, displayName);
    await saveAccessToken(result.access_token);
    setUser(result.user);
  }, []);

  const signOut = useCallback(async () => {
    await clearAccessToken();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signUp, signOut, refreshUser }),
    [user, loading, signIn, signUp, signOut, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
