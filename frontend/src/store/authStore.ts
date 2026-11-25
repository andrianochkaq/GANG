import { create } from 'zustand';

// unknown: not checked yet after a page load; the refresh cookie may still
// hold a session. The access token is kept in memory only (architecture.md, D4).
export type AuthStatus = 'unknown' | 'authenticated' | 'anonymous';

type AuthState = {
  accessToken: string | null;
  status: AuthStatus;
  setSession: (accessToken: string) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  status: 'unknown',
  setSession: (accessToken) => set({ accessToken, status: 'authenticated' }),
  clearSession: () => set({ accessToken: null, status: 'anonymous' }),
}));
