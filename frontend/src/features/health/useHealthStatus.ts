import { useQuery } from '@tanstack/react-query';

import { fetchHealthStatus } from '../../api/health';

export const HEALTH_QUERY_KEY = ['health'] as const;

export function useHealthStatus() {
  return useQuery({
    queryKey: HEALTH_QUERY_KEY,
    queryFn: fetchHealthStatus,
  });
}
