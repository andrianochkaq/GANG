// A fridge as the signed-in user sees it (GET /api/fridges/, FC-205).
export type FridgeRole = 'owner' | 'member';

export type Fridge = {
  id: string;
  name: string;
  role: FridgeRole;
  memberCount: number;
  productCount: number;
  // The fridge the user works in; the backend remembers it (last_fridge),
  // so it survives a reload and a second device.
  isCurrent: boolean;
};

// One contract for the real backend and the mock used with VITE_AUTH_MOCK=true.
export interface FridgesApi {
  listFridges(): Promise<Fridge[]>;
  createFridge(name: string): Promise<Fridge>;
  renameFridge(fridgeId: string, name: string): Promise<Fridge>;
  selectFridge(fridgeId: string): Promise<Fridge>;
}

// FridgeNameSerializer.name max_length on the backend.
export const FRIDGE_NAME_MAX_LENGTH = 100;
