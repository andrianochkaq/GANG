import { act, cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { useThemeStore } from '../store/themeStore';
import ThemeProvider from './ThemeProvider';
import { DEFAULT_THEME_ID, getTheme } from './themes';

function readRootToken(tokenName: string): string {
  return document.documentElement.style.getPropertyValue(`--${tokenName}`);
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    useThemeStore.setState({ themeId: DEFAULT_THEME_ID });
  });

  afterEach(() => {
    cleanup();
    document.documentElement.removeAttribute('style');
  });

  it('renders its children', () => {
    render(
      <ThemeProvider>
        <p>content</p>
      </ThemeProvider>,
    );
    expect(screen.getByText('content')).toBeTruthy();
  });

  it('writes the white theme to :root by default', () => {
    render(<ThemeProvider>{null}</ThemeProvider>);
    expect(readRootToken('bg')).toBe(getTheme('white').tokens.bg);
    expect(readRootToken('accent')).toBe(getTheme('white').tokens.accent);
  });

  it('recolours :root at once when the theme changes', () => {
    render(<ThemeProvider>{null}</ThemeProvider>);
    act(() => useThemeStore.getState().setThemeId('sakura'));
    const { tokens } = getTheme('sakura');
    expect(readRootToken('bg')).toBe(tokens.bg);
    expect(readRootToken('soft')).toBe(tokens.soft);
    expect(readRootToken('line')).toBe(tokens.line);
    expect(readRootToken('accent')).toBe(tokens.accent);
    expect(readRootToken('ink')).toBe(tokens.ink);
  });

  it('leaves the fixed colours alone', () => {
    render(<ThemeProvider>{null}</ThemeProvider>);
    act(() => useThemeStore.getState().setThemeId('cherry'));
    expect(readRootToken('text')).toBe('');
    expect(readRootToken('surface')).toBe('');
    expect(readRootToken('danger')).toBe('');
  });
});
