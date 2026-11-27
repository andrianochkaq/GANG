import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { fridgesApi } from '../../api/fridges';
import type { Fridge } from '../../api/fridgesTypes';

export const FRIDGES_QUERY_KEY = ['fridges'] as const;

// Every query that reads one fridge's data (products, lists, AI context)
// starts its key with this, so switching fridges gives new keys and the
// screens load the new fridge's data, and invalidating ['fridge'] refreshes
// all of it.
export function fridgeQueryKey(fridgeId: string, ...parts: readonly unknown[]) {
  return ['fridge', fridgeId, ...parts] as const;
}

// The user's fridges. gcTime 0 drops them when the protected area unmounts
// (logout), so the next account never sees them.
export function useFridges() {
  return useQuery({
    queryKey: FRIDGES_QUERY_KEY,
    queryFn: () => fridgesApi.listFridges(),
    gcTime: 0,
  });
}

export function findCurrentFridge(fridges: readonly Fridge[] | undefined): Fridge | undefined {
  return fridges?.find((fridge) => fridge.isCurrent) ?? fridges?.[0];
}

// The fridge the user works in now; undefined while the list loads.
export function useCurrentFridge(): Fridge | undefined {
  return findCurrentFridge(useFridges().data);
}

function markCurrent(fridges: readonly Fridge[], fridgeId: string): Fridge[] {
  return fridges.map((fridge) => ({ ...fridge, isCurrent: fridge.id === fridgeId }));
}

// Switching shows the new fridge at once and rolls back if the backend
// refuses; the backend's choice is kept for the next reload.
export function useSelectFridge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (fridgeId: string) => fridgesApi.selectFridge(fridgeId),
    onMutate: async (fridgeId) => {
      await queryClient.cancelQueries({ queryKey: FRIDGES_QUERY_KEY });
      const previous = queryClient.getQueryData<Fridge[]>(FRIDGES_QUERY_KEY);
      if (previous) {
        queryClient.setQueryData<Fridge[]>(FRIDGES_QUERY_KEY, markCurrent(previous, fridgeId));
      }
      return { previous };
    },
    onError: (_error, _fridgeId, context) => {
      if (context?.previous) {
        queryClient.setQueryData(FRIDGES_QUERY_KEY, context.previous);
      }
    },
    onSuccess: (fridge) => {
      queryClient.setQueryData<Fridge[]>(FRIDGES_QUERY_KEY, (fridges) =>
        fridges ? markCurrent(fridges, fridge.id) : fridges,
      );
      void queryClient.invalidateQueries({ queryKey: ['fridge'] });
    },
  });
}

function replaceFridge(fridges: readonly Fridge[] | undefined, fridge: Fridge) {
  return fridges?.map((item) =>
    item.id === fridge.id ? { ...fridge, isCurrent: item.isCurrent } : item,
  );
}

export function useRenameFridge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ fridgeId, name }: { fridgeId: string; name: string }) =>
      fridgesApi.renameFridge(fridgeId, name),
    onSuccess: (fridge) => {
      queryClient.setQueryData<Fridge[]>(FRIDGES_QUERY_KEY, (fridges) =>
        replaceFridge(fridges, fridge),
      );
    },
  });
}

export function useCreateFridge() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => fridgesApi.createFridge(name),
    onSuccess: (fridge) => {
      queryClient.setQueryData<Fridge[]>(FRIDGES_QUERY_KEY, (fridges) =>
        fridges ? [...fridges, { ...fridge, isCurrent: false }] : fridges,
      );
    },
  });
}
