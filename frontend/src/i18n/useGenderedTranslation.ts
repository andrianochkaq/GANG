import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

import { useUserStore } from '../store/userStore';
import { getGenderContext } from './gender';

// Translates a key with the current user's gender as i18next context.
export function useGenderedTranslation() {
  const { t } = useTranslation();
  const gender = useUserStore((state) => state.gender);
  const context = getGenderContext(gender);

  return useCallback((key: string) => t(key, { context }), [t, context]);
}
