// One name offered while typing (GET /api/fridges/<id>/items/suggestions/, FC-303).
export type ProductSuggestionSource = 'fridge' | 'catalog';

export type ProductSuggestion = {
  source: ProductSuggestionSource;
  name: string;
  unit: string;
  // Category slug.
  category: string;
  // Catalog link, or null for a name the fridge has but the catalog does not.
  catalogProduct: string | null;
};

export interface ProductsApi {
  suggestProducts(fridgeId: string, text: string): Promise<ProductSuggestion[]>;
}

// ProductSuggestionQuerySerializer.q max_length on the backend.
export const PRODUCT_SEARCH_MAX_LENGTH = 120;
