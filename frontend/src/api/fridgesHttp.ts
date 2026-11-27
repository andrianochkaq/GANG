import { z } from 'zod';

import { toAuthApiError } from './authErrors';
import { apiClient } from './client';
import type { Fridge, FridgesApi } from './fridgesTypes';

export const FRIDGES_PATH = '/api/fridges/';

export function fridgePath(fridgeId: string): string {
  return `${FRIDGES_PATH}${encodeURIComponent(fridgeId)}/`;
}

const fridgeSchema = z.object({
  id: z.string(),
  name: z.string(),
  role: z.enum(['owner', 'member']).catch('member'),
  member_count: z.number().int().nonnegative(),
  product_count: z.number().int().nonnegative(),
  is_current: z.boolean(),
});

export function toFridge(data: unknown): Fridge {
  const parsed = fridgeSchema.parse(data);
  return {
    id: parsed.id,
    name: parsed.name,
    role: parsed.role,
    memberCount: parsed.member_count,
    productCount: parsed.product_count,
    isCurrent: parsed.is_current,
  };
}

async function send<T>(request: () => Promise<{ data: unknown }>, parse: (data: unknown) => T) {
  try {
    const response = await request();
    return parse(response.data);
  } catch (error) {
    throw toAuthApiError(error);
  }
}

export const httpFridgesApi: FridgesApi = {
  listFridges() {
    return send(
      () => apiClient.get(FRIDGES_PATH),
      (data) => z.array(z.unknown()).parse(data).map(toFridge),
    );
  },
  createFridge(name) {
    return send(() => apiClient.post(FRIDGES_PATH, { name }), toFridge);
  },
  renameFridge(fridgeId, name) {
    return send(() => apiClient.patch(fridgePath(fridgeId), { name }), toFridge);
  },
  selectFridge(fridgeId) {
    return send(() => apiClient.post(`${fridgePath(fridgeId)}select/`), toFridge);
  },
};
