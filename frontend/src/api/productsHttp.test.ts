import { describe, expect, it } from 'vitest';

import { suggestionsPath, toProductSuggestions } from './productsHttp';

describe('productsHttp', () => {
  it('builds the suggestions path of a fridge', () => {
    expect(suggestionsPath('abc')).toBe('/api/fridges/abc/items/suggestions/');
  });

  it('turns snake_case rows into suggestions', () => {
    const result = toProductSuggestions({
      suggestions: [
        {
          source: 'fridge',
          name: 'Молоко',
          unit: 'l',
          category: 'dairy',
          catalog_product: null,
        },
        {
          source: 'catalog',
          name: 'Морква',
          unit: 'kg',
          category: 'veg',
          catalog_product: 'id-1',
        },
      ],
    });
    expect(result).toEqual([
      {
        source: 'fridge',
        name: 'Молоко',
        unit: 'l',
        category: 'dairy',
        catalogProduct: null,
      },
      {
        source: 'catalog',
        name: 'Морква',
        unit: 'kg',
        category: 'veg',
        catalogProduct: 'id-1',
      },
    ]);
  });

  it('rejects a body without the suggestions list', () => {
    expect(() => toProductSuggestions({})).toThrow();
  });
});
