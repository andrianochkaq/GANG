import { useAuthStore } from '../store/authStore';
import { authApi } from './auth';
import type { AuthApi } from './authTypes';

let pendingRefresh: Promise<string | null> | null = null;

// One refresh at a time: parallel 401s and the first page load share it.
export function refreshAccessToken(api: AuthApi = authApi): Promise<string | null> {
  if (!pendingRefresh) {
    pendingRefresh = api
      .refreshSession()
      .then(({ access }) => {
        useAuthStore.getState().setSession(access);
        return access;
      })
      .catch(() => {
        useAuthStore.getState().clearSession();
        return null;
      })
      .finally(() => {
        pendingRefresh = null;
      });
  }
  return pendingRefresh;
}

export function startSession(access: string): void {
  useAuthStore.getState().setSession(access);
}
