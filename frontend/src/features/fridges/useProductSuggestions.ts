import { keepPreviousData, useQuery } from '@tanstack/react-query';

import { productsApi } from '../../api/products';
import { useDebouncedValue } from '../../hooks/useDebouncedValue';
import { fridgeQueryKey } from './useFridges';

export const SUGGESTION_DEBOUNCE_MS = 200;
const SUGGESTION_STALE_MS = 30_000;

// Suggestions for the text typed so far. The request waits until typing
// pauses for 200 ms, so fast typing sends at most one request per 200 ms.
export function useProductSuggestions(fridgeId: string, text: string) {
  const debouncedText = useDebouncedValue(text.trim(), SUGGESTION_DEBOUNCE_MS);
  const query = useQuery({
    queryKey: fridgeQueryKey(fridgeId, 'suggestions', debouncedText),
    queryFn: () => productsApi.suggestProducts(fridgeId, debouncedText),
    enabled: debouncedText.length > 0,
    staleTime: SUGGESTION_STALE_MS,
    placeholderData: keepPreviousData,
  });
  const isWaiting = text.trim() !== debouncedText;
  return {
    suggestions: debouncedText.length > 0 ? (query.data ?? []) : [],
    isLoading: debouncedText.length > 0 && (isWaiting || query.isFetching),
    isError: query.isError,
    hasSettled: debouncedText.length > 0 && !isWaiting && query.isSuccess && !query.isFetching,
  };
}
