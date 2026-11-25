import { httpAuthApi } from './authHttp';
import { createMockAuthApi } from './authMock';
import type { AuthApi } from './authTypes';

export function isAuthMockEnabled(flag: string | undefined): boolean {
  return (flag ?? '').trim().toLowerCase() === 'true';
}

// VITE_AUTH_MOCK=true runs the auth screens without the backend.
export const authApi: AuthApi = isAuthMockEnabled(import.meta.env.VITE_AUTH_MOCK)
  ? createMockAuthApi()
  : httpAuthApi;
