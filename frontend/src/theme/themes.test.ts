import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

import uk from '../i18n/uk.json';
import {
  DEFAULT_THEME_ID,
  MIN_ACCENT_CONTRAST,
  THEMES,
  applyThemeTokens,
  buildThemeTokens,
  getContrastRatio,
  getTheme,
  isThemeId,
  mixTowardBlack,
  mixTowardWhite,
  type ThemeId,
  type ThemeTokens,
} from './themes';

// The table from docs/design-system/01-theming.md, written out here so the test
// does not depend on the docs folder being mounted next to the frontend.
const EXPECTED_TOKENS: Record<ThemeId, ThemeTokens> = {
  white: { bg: '#f7f5f0', soft: '#ece8e0', line: '#e4dfd5', accent: '#2f2e2b', ink: '#2f2e2b' },
  ocean: { bg: '#e9eef6', soft: '#c1cfe5', line: '#b1c3de', accent: '#506e99', ink: '#384d6b' },
  sky: { bg: '#f3f9fd', soft: '#ddeef9', line: '#d4eaf7', accent: '#5a7180', ink: '#3f4f5a' },
  lilac: { bg: '#faf6fb', soft: '#efe4f4', line: '#ecdef1', accent: '#736479', ink: '#504655' },
  lavender: { bg: '#f4f2f8', soft: '#dfdaec', line: '#d8d1e7', accent: '#736b87', ink: '#504b5e' },
  emerald: { bg: '#e6eae6', soft: '#b7c3b9', line: '#a4b4a8', accent: '#4a6a50', ink: '#344a38' },
  summer: { bg: '#eff4ed', soft: '#d1dfcb', line: '#c6d8be', accent: '#5d7353', ink: '#41503a' },
  sprout: { bg: '#fafbf6', soft: '#f1f5e4', line: '#eef2de', accent: '#696d5a', ink: '#4a4c3f' },
  lime: { bg: '#f9fbe7', soft: '#eef3bc', line: '#eaf0ab', accent: '#666c29', ink: '#474c1d' },
  cinnamon: { bg: '#f3ebe5', soft: '#dbc5b4', line: '#d2b6a2', accent: '#95633d', ink: '#68452b' },
  sunset: { bg: '#fdf5e8', soft: '#f9e3bf', line: '#f8dcae', accent: '#806232', ink: '#5a4523' },
  peach: { bg: '#fefbef', soft: '#fbf2d0', line: '#faefc4', accent: '#756b43', ink: '#524b2f' },
  lemon: { bg: '#fffeed', soft: '#fffdcc', line: '#fffcbf', accent: '#6e6c37', ink: '#4d4c26' },
  burgundy: { bg: '#f4e2e6', soft: '#dfadb7', line: '#d899a4', accent: '#b0334a', ink: '#7b2434' },
  cherry: { bg: '#fbeceb', soft: '#f3cac6', line: '#f0bcb8', accent: '#a45952', ink: '#733e39' },
  sakura: { bg: '#fdf8fa', soft: '#faebf1', line: '#f8e6ed', accent: '#806d74', ink: '#5a4c51' },
  fog: { bg: '#f7f7f7', soft: '#e9e9e9', line: '#e4e4e4', accent: '#6a6a6a', ink: '#4a4a4a' },
};

const MIN_TEXT_CONTRAST = 4.5; // WCAG AA, normal text
const MIN_UI_CONTRAST = 3; // WCAG AA, focus ring and other non-text parts
const TOKENS_CSS = readFileSync(join(__dirname, 'tokens.css'), 'utf8');

// Fixed colours (they never change with the theme) are read from tokens.css.
function readFixedColor(tokenName: string): string {
  const match = TOKENS_CSS.match(new RegExp(`--${tokenName}:\\s*(#[0-9a-fA-F]{6})`));
  if (!match) {
    throw new Error(`--${tokenName} is missing in tokens.css`);
  }
  return match[1];
}

const TEXT = readFixedColor('text');
const TEXT_SECONDARY = readFixedColor('text-secondary');
const TEXT_MUTED = readFixedColor('text-muted');
const TEXT_SUBTLE = readFixedColor('text-subtle');
const SURFACE = readFixedColor('surface');
const ON_ACCENT = readFixedColor('on-accent');

describe('theme list', () => {
  it('has the 17 app colours with white first and default', () => {
    expect(THEMES).toHaveLength(17);
    expect(THEMES[0].id).toBe('white');
    expect(DEFAULT_THEME_ID).toBe('white');
    expect(new Set(THEMES.map((theme) => theme.id)).size).toBe(17);
  });

  it('gives every theme a Ukrainian name in uk.json', () => {
    THEMES.forEach((theme) => {
      expect(uk.theme.colors[theme.id]).toBeTruthy();
    });
  });

  it('sets every themed token on every theme', () => {
    THEMES.forEach((theme) => {
      expect(Object.keys(theme.tokens).sort()).toEqual(['accent', 'bg', 'ink', 'line', 'soft']);
      Object.values(theme.tokens).forEach((value) => expect(value).toMatch(/^#[0-9a-f]{6}$/));
    });
  });

  it('matches the table in the theming guide', () => {
    THEMES.forEach((theme) => {
      expect(theme.tokens, theme.id).toEqual(EXPECTED_TOKENS[theme.id]);
    });
  });

  it('finds a theme by id and recognises theme ids', () => {
    expect(getTheme('ocean').tokens.accent).toBe('#506e99');
    expect(isThemeId('sakura')).toBe(true);
    expect(isThemeId('green')).toBe(false);
  });
});

describe('theme formula', () => {
  it('mixes toward white and black', () => {
    expect(mixTowardWhite('#000000', 0.5)).toBe('#808080');
    expect(mixTowardBlack('#ffffff', 0.1)).toBe('#e6e6e6');
  });

  it('uses the fixed warm palette for white', () => {
    expect(buildThemeTokens('#FFFFFF')).toEqual(EXPECTED_TOKENS.white);
  });

  it('keeps an accent that already has enough contrast', () => {
    expect(buildThemeTokens('#4a6a50').accent).toBe('#4a6a50');
  });

  it('darkens a light accent until white text reads on it', () => {
    const { accent } = buildThemeTokens('#fff97f');
    expect(accent).not.toBe('#fff97f');
    expect(getContrastRatio(ON_ACCENT, accent)).toBeGreaterThanOrEqual(MIN_ACCENT_CONTRAST);
  });

  it('rejects a colour that is not a six-digit hex', () => {
    expect(() => buildThemeTokens('red')).toThrow();
  });
});

describe('contrast of every theme (WCAG AA)', () => {
  THEMES.forEach((theme) => {
    const { bg, soft, accent, ink } = theme.tokens;

    it(`${theme.id}: text reads on the page background`, () => {
      [TEXT, TEXT_SECONDARY, TEXT_MUTED, TEXT_SUBTLE].forEach((color) => {
        expect(getContrastRatio(color, bg)).toBeGreaterThanOrEqual(MIN_TEXT_CONTRAST);
      });
    });

    it(`${theme.id}: text reads on soft fills`, () => {
      // text-subtle is never placed on soft (04-agent-checklist.md).
      [TEXT, TEXT_SECONDARY, TEXT_MUTED].forEach((color) => {
        expect(getContrastRatio(color, soft)).toBeGreaterThanOrEqual(MIN_TEXT_CONTRAST);
      });
    });

    it(`${theme.id}: ink reads on bg and soft`, () => {
      expect(getContrastRatio(ink, bg)).toBeGreaterThanOrEqual(MIN_TEXT_CONTRAST);
      expect(getContrastRatio(ink, soft)).toBeGreaterThanOrEqual(MIN_TEXT_CONTRAST);
    });

    it(`${theme.id}: white text reads on the accent`, () => {
      expect(getContrastRatio(ON_ACCENT, accent)).toBeGreaterThanOrEqual(MIN_TEXT_CONTRAST);
    });

    it(`${theme.id}: the accent stands out as a focus ring and fill`, () => {
      expect(getContrastRatio(accent, bg)).toBeGreaterThanOrEqual(MIN_UI_CONTRAST);
      expect(getContrastRatio(accent, SURFACE)).toBeGreaterThanOrEqual(MIN_UI_CONTRAST);
    });
  });
});

describe('applyThemeTokens', () => {
  it('writes the five tokens as CSS variables on the target', () => {
    const target = document.createElement('div');
    applyThemeTokens(getTheme('ocean').tokens, target);
    expect(target.style.getPropertyValue('--bg')).toBe('#e9eef6');
    expect(target.style.getPropertyValue('--soft')).toBe('#c1cfe5');
    expect(target.style.getPropertyValue('--line')).toBe('#b1c3de');
    expect(target.style.getPropertyValue('--accent')).toBe('#506e99');
    expect(target.style.getPropertyValue('--ink')).toBe('#384d6b');
  });
});
