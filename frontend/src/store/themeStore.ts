import { create } from 'zustand';

import { DEFAULT_THEME_ID, type ThemeId } from '../theme/themes';

type ThemeState = {
  themeId: ThemeId;
  setThemeId: (themeId: ThemeId) => void;
};

// The choice will be loaded from the profile once accounts land (FC-202).
export const useThemeStore = create<ThemeState>((set) => ({
  themeId: DEFAULT_THEME_ID,
  setThemeId: (themeId) => set({ themeId }),
}));
