/** Poll sync while a screen is focused and online (ADR-004, 5s interval). */
import NetInfo from '@react-native-community/netinfo';
import { useFocusEffect } from '@react-navigation/native';
import { useCallback, useRef } from 'react';

import { runSync } from './syncEngine';

const POLL_MS = 5000;

export function useRealtimeSync(
  familyId: string,
  onSynced?: () => void,
): void {
  const onSyncedRef = useRef(onSynced);
  onSyncedRef.current = onSynced;

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      let timer: ReturnType<typeof setInterval> | null = null;

      const tick = async () => {
        const state = await NetInfo.fetch();
        if (!state.isConnected || cancelled) {
          return;
        }
        await runSync(familyId);
        if (!cancelled) {
          onSyncedRef.current?.();
        }
      };

      tick().catch(() => undefined);
      timer = setInterval(() => {
        tick().catch(() => undefined);
      }, POLL_MS);

      return () => {
        cancelled = true;
        if (timer) {
          clearInterval(timer);
        }
      };
    }, [familyId]),
  );
}
