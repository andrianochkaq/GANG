import { isAuthMockEnabled } from './auth';
import { httpFridgesApi } from './fridgesHttp';
import { createMockFridgesApi } from './fridgesMock';
import type { FridgesApi } from './fridgesTypes';

// VITE_AUTH_MOCK=true runs the fridges without the backend, like the profile.
export const fridgesApi: FridgesApi = isAuthMockEnabled(import.meta.env.VITE_AUTH_MOCK)
  ? createMockFridgesApi()
  : httpFridgesApi;
