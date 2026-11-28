import { isAuthMockEnabled } from './auth';
import { httpProductsApi } from './productsHttp';
import { createMockProductsApi } from './productsMock';
import type { ProductsApi } from './productsTypes';

// VITE_AUTH_MOCK=true runs the product suggestions without the backend.
export const productsApi: ProductsApi = isAuthMockEnabled(import.meta.env.VITE_AUTH_MOCK)
  ? createMockProductsApi()
  : httpProductsApi;
