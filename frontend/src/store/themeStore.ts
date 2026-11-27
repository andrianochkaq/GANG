import { create } from 'zustand';

import { DEFAULT_THEME_ID, type ThemeId } from '../theme/themes';

type ThemeState = {
  themeId: ThemeId;
  setThemeId: (themeId: ThemeId) => void;
};

// The saved choice is loaded from /api/me/ by ProfileGate after every login.
export const useThemeStore = create<ThemeState>((set) => ({
  themeId: DEFAULT_THEME_ID,
  setThemeId: (themeId) => set({ themeId }),
}));
