import { useLayoutEffect, type ReactNode } from 'react';

import { useThemeStore } from '../store/themeStore';
import { applyThemeTokens, getTheme } from './themes';

type ThemeProviderProps = {
  children: ReactNode;
};

// Keeps the five themed CSS variables on :root in sync with the chosen theme.
export default function ThemeProvider({ children }: ThemeProviderProps) {
  const themeId = useThemeStore((state) => state.themeId);

  useLayoutEffect(() => {
    applyThemeTokens(getTheme(themeId).tokens);
  }, [themeId]);

  return <>{children}</>;
}
