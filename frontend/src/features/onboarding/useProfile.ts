import { useQuery } from '@tanstack/react-query';

import { profileApi } from '../../api/profile';

export const PROFILE_QUERY_KEY = ['me'] as const;

// The signed-in user's profile. gcTime 0 drops it as soon as the protected
// area unmounts (logout, expired session), so the next account never sees it.
export function useProfile() {
  return useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: () => profileApi.getProfile(),
    gcTime: 0,
  });
}
