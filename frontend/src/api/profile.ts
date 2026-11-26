import { isAuthMockEnabled } from './auth';
import { httpProfileApi } from './profileHttp';
import { createMockProfileApi } from './profileMock';
import type { ProfileApi } from './profileTypes';

// VITE_AUTH_MOCK=true runs the profile without the backend, like the auth screens.
export const profileApi: ProfileApi = isAuthMockEnabled(import.meta.env.VITE_AUTH_MOCK)
  ? createMockProfileApi()
  : httpProfileApi;
