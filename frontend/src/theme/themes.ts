// Theme engine data (docs/design-system/01-theming.md). The user picks one of
// 17 app colours; five tokens are derived from it and written to :root.
// All other colours (text, surface, status, ...) never change with the theme.

export type ThemeId =
  | 'white'
  | 'ocean'
  | 'sky'
  | 'lilac'
  | 'lavender'
  | 'emerald'
  | 'summer'
  | 'sprout'
  | 'lime'
  | 'cinnamon'
  | 'sunset'
  | 'peach'
  | 'lemon'
  | 'burgundy'
  | 'cherry'
  | 'sakura'
  | 'fog';

export type ThemeTokens = {
  bg: string;
  soft: string;
  line: string;
  accent: string;
  ink: string;
};

export type Theme = {
  id: ThemeId;
  swatch: string;
  tokens: ThemeTokens;
};

export const DEFAULT_THEME_ID: ThemeId = 'white';

// Order and names are fixed by the ColorPicker (names live in uk.json, theme.colors.<id>).
const THEME_SWATCHES: ReadonlyArray<{ id: ThemeId; swatch: string }> = [
  { id: 'white', swatch: '#ffffff' },
  { id: 'ocean', swatch: '#6387bd' },
  { id: 'sky', swatch: '#a9d4ef' },
  { id: 'lilac', swatch: '#d8bce3' },
  { id: 'lavender', swatch: '#b0a3cf' },
  { id: 'emerald', swatch: '#4a6a50' },
  { id: 'summer', swatch: '#8db07e' },
  { id: 'sprout', swatch: '#dce5bc' },
  { id: 'lime', swatch: '#d4e157' },
  { id: 'cinnamon', swatch: '#a66e44' },
  { id: 'sunset', swatch: '#f0b95e' },
  { id: 'peach', swatch: '#f6df8a' },
  { id: 'lemon', swatch: '#fff97f' },
  { id: 'burgundy', swatch: '#b0334a' },
  { id: 'cherry', swatch: '#e07a70' },
  { id: 'sakura', swatch: '#f2cedb' },
  { id: 'fog', swatch: '#c8c8c8' },
];

// Білий is special: a warm neutral instead of a tint of pure white.
const WHITE_SWATCH = '#ffffff';
const WHITE_TOKENS: ThemeTokens = {
  bg: '#f7f5f0',
  soft: '#ece8e0',
  line: '#e4dfd5',
  accent: '#2f2e2b',
  ink: '#2f2e2b',
};

const WHITE_HEX = '#ffffff';
const WHITE_CHANNEL = 255;
const BLACK_CHANNEL = 0;
const BG_MIX = 0.86;
const SOFT_MIX = 0.6;
const LINE_MIX = 0.5;
const DARKEN_AMOUNT = 0.1;
const INK_DARKEN_AMOUNT = 0.3;
// Contrast of white text on the accent; a little above AA (4.5) as a margin.
export const MIN_ACCENT_CONTRAST = 4.8;
const MAX_DARKEN_STEPS = 30;
const HEX_COLOR_PATTERN = /^#[0-9a-f]{6}$/i;

function parseHexChannels(hex: string): number[] {
  if (!HEX_COLOR_PATTERN.test(hex)) {
    throw new Error(`Invalid hex colour: ${hex}`);
  }
  return [1, 3, 5].map((start) => parseInt(hex.slice(start, start + 2), 16));
}

// Half-to-even rounding reproduces the 17 values of the theming table exactly;
// Math.round (half up) would be one channel step off in a few of them.
function roundHalfToEven(value: number): number {
  const lower = Math.floor(value);
  const rest = value - lower;
  if (rest === 0.5) {
    return lower % 2 === 0 ? lower : lower + 1;
  }
  return Math.round(value);
}

function mixTowardChannel(hex: string, targetChannel: number, amount: number): string {
  const channels = parseHexChannels(hex).map((channel) =>
    roundHalfToEven(channel + (targetChannel - channel) * amount),
  );
  return `#${channels.map((channel) => channel.toString(16).padStart(2, '0')).join('')}`;
}

export function mixTowardWhite(hex: string, amount: number): string {
  return mixTowardChannel(hex, WHITE_CHANNEL, amount);
}

export function mixTowardBlack(hex: string, amount: number): string {
  return mixTowardChannel(hex, BLACK_CHANNEL, amount);
}

function linearizeChannel(channel: number): number {
  const value = channel / 255;
  return value <= 0.03928 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
}

function getRelativeLuminance(hex: string): number {
  const [red, green, blue] = parseHexChannels(hex).map(linearizeChannel);
  return red * 0.2126 + green * 0.7152 + blue * 0.0722;
}

// WCAG 2.x contrast ratio, from 1 (same colour) to 21 (black on white).
export function getContrastRatio(firstHex: string, secondHex: string): number {
  const firstLuminance = getRelativeLuminance(firstHex);
  const secondLuminance = getRelativeLuminance(secondHex);
  return (
    (Math.max(firstLuminance, secondLuminance) + 0.05) /
    (Math.min(firstLuminance, secondLuminance) + 0.05)
  );
}

export function buildThemeTokens(swatch: string): ThemeTokens {
  const base = swatch.toLowerCase();
  if (base === WHITE_SWATCH) {
    return { ...WHITE_TOKENS };
  }
  let accent = base;
  let steps = 0;
  while (steps < MAX_DARKEN_STEPS && getContrastRatio(accent, WHITE_HEX) < MIN_ACCENT_CONTRAST) {
    accent = mixTowardBlack(accent, DARKEN_AMOUNT);
    steps += 1;
  }
  return {
    bg: mixTowardWhite(base, BG_MIX),
    soft: mixTowardWhite(base, SOFT_MIX),
    line: mixTowardWhite(base, LINE_MIX),
    accent,
    ink: mixTowardBlack(accent, INK_DARKEN_AMOUNT),
  };
}

export const THEMES: readonly Theme[] = THEME_SWATCHES.map(({ id, swatch }) => ({
  id,
  swatch,
  tokens: buildThemeTokens(swatch),
}));

export function isThemeId(value: string): value is ThemeId {
  return THEMES.some((theme) => theme.id === value);
}

export function getTheme(themeId: ThemeId): Theme {
  return THEMES.find((theme) => theme.id === themeId) ?? THEMES[0];
}

// Writing to :root recolours every screen at once; the CSS reads var(--bg) etc.
export function applyThemeTokens(
  tokens: ThemeTokens,
  target: HTMLElement = document.documentElement,
): void {
  (Object.keys(tokens) as Array<keyof ThemeTokens>).forEach((tokenName) => {
    target.style.setProperty(`--${tokenName}`, tokens[tokenName]);
  });
}
