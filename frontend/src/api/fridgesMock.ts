import i18n from '../i18n';
import type { Fridge, FridgesApi } from './fridgesTypes';

// In-memory stand-in for /api/fridges/, switched on with VITE_AUTH_MOCK=true.
// Like the backend, every account starts with one fridge it owns.
const RESPONSE_DELAY_MS = 300;

let fridges: Fridge[] = [];
let nextId = 1;

function createFridgeRow(name: string): Fridge {
  const id = `00000000-0000-4000-8000-${String(nextId++).padStart(12, '0')}`;
  return { id, name, role: 'owner', memberCount: 1, productCount: 0, isCurrent: false };
}

function ensureDefaultFridge(): void {
  if (fridges.length === 0) {
    fridges = [{ ...createFridgeRow(i18n.t('fridges.mockDefaultName')), isCurrent: true }];
  }
}

function wait(delayMs: number): Promise<void> {
  return delayMs > 0 ? new Promise((resolve) => setTimeout(resolve, delayMs)) : Promise.resolve();
}

function findFridge(fridgeId: string): Fridge {
  const fridge = fridges.find((item) => item.id === fridgeId);
  if (!fridge) {
    throw new Error(`No fridge ${fridgeId}`);
  }
  return fridge;
}

export function resetFridgesMock(rows: Fridge[] = []): void {
  fridges = rows.map((row) => ({ ...row }));
}

export function createMockFridgesApi(delayMs = RESPONSE_DELAY_MS): FridgesApi {
  return {
    async listFridges() {
      await wait(delayMs);
      ensureDefaultFridge();
      return fridges.map((row) => ({ ...row }));
    },
    async createFridge(name) {
      await wait(delayMs);
      ensureDefaultFridge();
      const fridge = createFridgeRow(name);
      fridges = [...fridges, fridge];
      return { ...fridge };
    },
    async renameFridge(fridgeId, name) {
      await wait(delayMs);
      fridges = fridges.map((row) => (row.id === fridgeId ? { ...row, name } : row));
      return { ...findFridge(fridgeId) };
    },
    async selectFridge(fridgeId) {
      await wait(delayMs);
      findFridge(fridgeId);
      fridges = fridges.map((row) => ({ ...row, isCurrent: row.id === fridgeId }));
      return { ...findFridge(fridgeId) };
    },
  };
}
