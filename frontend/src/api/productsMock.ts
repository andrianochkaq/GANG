import i18n from '../i18n';
import type { ProductSuggestion, ProductsApi } from './productsTypes';

// In-memory stand-in for the suggestions endpoint, switched on with
// VITE_AUTH_MOCK=true. It matches names that start with the text.
const RESPONSE_DELAY_MS = 150;
const MAX_SUGGESTIONS = 8;

const CATALOG: Array<Omit<ProductSuggestion, 'name'> & { nameKey: string }> = [
  { source: 'catalog', nameKey: 'milk', unit: 'l', category: 'dairy', catalogProduct: null },
  { source: 'catalog', nameKey: 'carrot', unit: 'kg', category: 'veg', catalogProduct: null },
  { source: 'catalog', nameKey: 'honey', unit: 'g', category: 'sweet', catalogProduct: null },
  { source: 'catalog', nameKey: 'butter', unit: 'g', category: 'dairy', catalogProduct: null },
  { source: 'catalog', nameKey: 'cheese', unit: 'g', category: 'dairy', catalogProduct: null },
  { source: 'catalog', nameKey: 'eggs', unit: 'pcs', category: 'egg', catalogProduct: null },
];

function wait(delayMs: number): Promise<void> {
  return delayMs > 0 ? new Promise((resolve) => setTimeout(resolve, delayMs)) : Promise.resolve();
}

export function createMockProductsApi(delayMs = RESPONSE_DELAY_MS): ProductsApi {
  return {
    async suggestProducts(_fridgeId, text) {
      await wait(delayMs);
      const start = text.trim().toLocaleLowerCase('uk');
      if (!start) {
        return [];
      }
      return CATALOG.map(({ nameKey, ...row }) => ({
        ...row,
        name: i18n.t(`productSearch.mock.${nameKey}`),
      }))
        .filter((row) => row.name.toLocaleLowerCase('uk').startsWith(start))
        .slice(0, MAX_SUGGESTIONS);
    },
  };
}
