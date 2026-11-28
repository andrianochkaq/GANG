import { z } from 'zod';

import { toAuthApiError } from './authErrors';
import { apiClient } from './client';
import { fridgePath } from './fridgesHttp';
import type { ProductSuggestion, ProductsApi } from './productsTypes';

export function suggestionsPath(fridgeId: string): string {
  return `${fridgePath(fridgeId)}items/suggestions/`;
}

const suggestionSchema = z.object({
  source: z.enum(['fridge', 'catalog']).catch('catalog'),
  name: z.string(),
  unit: z.string(),
  category: z.string(),
  catalog_product: z.string().nullable(),
});

const suggestionListSchema = z.object({ suggestions: z.array(suggestionSchema) });

export function toProductSuggestions(data: unknown): ProductSuggestion[] {
  return suggestionListSchema.parse(data).suggestions.map((row) => ({
    source: row.source,
    name: row.name,
    unit: row.unit,
    category: row.category,
    catalogProduct: row.catalog_product,
  }));
}

export const httpProductsApi: ProductsApi = {
  async suggestProducts(fridgeId, text) {
    try {
      const response = await apiClient.get(suggestionsPath(fridgeId), { params: { q: text } });
      return toProductSuggestions(response.data);
    } catch (error) {
      throw toAuthApiError(error);
    }
  },
};
