> **In this repository:** tokens are in `docs/design-system/tokens.json`, the canonical component CSS (`fc-*` classes) in `docs/design-system/components.css`, and each component's guidelines in `docs/design-system/components/<Name>.md`. Live previews: https://claude.ai/artifact/92ajfpnXHGb7A6Kj4rhFrM

FreeCook is a warm, calm kitchen app: white rounded cards float on a softly tinted page, one action colour comes from the user's chosen app colour, and a friendly fridge mascot is the face of the brand. Everything is Ukrainian, generous in size, and readable at arm's length in a kitchen.

**Read this file first, then the sections Theming, Layout and screens, Content and voice and Agent checklist, then the README of each component you use.** These rules win over anything you remember about other design systems.

## Sources and priority

1. `tokens.json` — every colour, size, radius, spacing, shadow and type style. Use tokens by name; never hard-code a value that has a token.
2. This brand book and its sections — how to use the tokens.
3. `components/<Name>/README.md` + `preview.html` — exact anatomy per component; `components/bundle.css` is the canonical CSS (`fc-*` classes).
4. The design canvas, for layout of whole screens: https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt
   - Mobile: use the **«Версія 3»** boards; where a screen has no version 3 board, the **«Версія 2»** board is current.
   - Desktop: use the **«Стало … (десктоп)»** boards for layout, with version 3 behaviour (the theme tints the whole app; the Calories tab only when enabled).
   - Never copy from **«Було»** boards. Ignore the fixed green accent `#3F6B4A` that version 2 and desktop boards use as a placeholder: the action colour is always the theme's `accent`.

If a screen needs something none of these define, compose it from existing components and tokens and say what you added. Do not invent new colours, fonts, radii or shadows.

## Golden rules

1. **Page = `bg`, blocks = `surface` cards with `radius-card` (22 px).** No borders on cards, no shadows except `shadow-tab` (selected segment) and `shadow-sheet` (sheets and dialogs).
2. **One `accent` action per screen**: a full-width 52 px primary button at the bottom of the content, or the send button in chat. Everything else is secondary, plain, tonal or text.
3. **The theme tints everything.** `bg`, `soft`, `line`, `accent` and `ink` change with the user's app colour; all screens must use these tokens so a theme switch recolours the whole app at once. White (Білий) is the default.
4. **Fixed colours stay fixed**: text greys, `surface`, status colours, category colours, water blues and `danger` are the same in every theme.
5. **Status is always written in words** — «до завтра», «2 дні», «у нормі», «замало» — the colour only repeats it.
6. **Touch targets ≥ 44 px.** Primary controls 52 px, compact 48, icon buttons 44, steppers and tabs 40 (inside rows only), chips 36 (in rows with gaps).
7. **Rubik 600 for headings and numbers, Inter for everything else.** No other fonts, no italics except the «i» hint glyph.
8. **Real labels and semantics**: `<button>`, `<a href>`, `<label>` + `<input>`; `aria-label` on every icon-only control; `role="switch"`, `tablist`, `radiogroup`, `dialog` where they apply.
9. **Ukrainian copy, sentence case, no emoji.** The UI says «ви»; the AI Chef says «ти». Names: «FreeCook», «AI-кухар» (never «ШІ»).
10. **Fit the phone.** Mobile screens are designed to fit one 844 px height; scroll only content lists, never the header or the primary button.

## Visual foundations

### Colour

| Role | Tokens | Rule |
| --- | --- | --- |
| Page | `bg` | Behind everything. Theme-tinted. |
| Blocks | `surface` | Cards, list groups, inputs, nav bar, sheets, AI bubbles. |
| Tinted fill | `soft` | Hero fridge card, segmented track, info badges, stepper buttons, avatar on profile, active nav pill. |
| Action | `accent` + `on-accent` | Primary buttons, user chat bubble, active list tab, checked controls, progress fills, focus ring. Never for text on light grounds. |
| Tinted text | `ink` | Links («Усі», «Змінити», «Списати»), active nav label, positive status words. |
| Hairlines | `line`, `divider`, `border-input` | `line` for theme-tinted outlines (chips, chat input, nav top border, progress track); `divider` between rows; `border-input` around inputs and secondary buttons. |
| Text | `text` › `text-secondary` › `text-muted` › `text-subtle` | Titles and values › supporting sentences and group labels › row meta › hints, timers, inactive nav. |
| Danger | `danger` | Text only: «Вийти», «Видалити», trash icons. |
| Expiry | `status-urgent-*`, `status-soon-*`, `status-ok-*` | Badges by days left: ≤ 1 day, 2–3 days, 4+ days. `status-soon-*` also for warnings. |
| Categories | `cat-veg-*`, `cat-dairy-*`, `cat-meat-*`, `cat-fruit-*`, `cat-sweet-*`, `cat-other-*` | Category chips and icon tiles only. |
| Water | `water-bg`, `water-fill`, `water-text`, `water-ink` | Water page and header pill. Water is always blue. |
| Palette | `swatch-*` | Only inside the colour picker; feed into the theme formula. |

Every text token reads at 4.5:1 or better on `bg`, `soft` and `surface` in every theme, and `on-accent` on `accent` at 4.8:1 or better. Keep these pairs; do not put `text-subtle` on `soft` or `ink` on `accent`.

### Typography

- Families: `display` = Rubik (headings, numbers, wordmark) and `text` = Inter (all UI text). Load from Google Fonts with Cyrillic: `https://fonts.googleapis.com/css2?family=Rubik:wght@400..700&family=Inter:wght@400;500;600&display=swap`.
- Use the type styles by name: `h1-desktop` 32, `h1` 28 (home greeting, onboarding), `h1-screen` 24 (tab screen titles, sheet titles), `h1-sub` 22 (sub-screen titles, wordmark), `h2` 18 (recipe and desktop card titles), `h2-sm` 16 (mobile card titles), numbers `stat-xl` 52 / `water-total` 40 / `stat` 34.
- Body styles: `input` 16 (inputs, list items, primary button labels at 600), `body` 15, `body-strong` 15 / 600 (product names), `label` 14 / 600 (form labels, small buttons), `row` 14, `meta` 13, `meta-strong` 13 / 600 (inline links, step labels), `badge` 12 / 600, `nav` 12 / 500.
- Headings: line-height 1.15; body: 1.4–1.45. Weights: 400, 500 (nav only), 600. Never 700 in UI text.
- Inputs are 16 px so iOS does not zoom.

### Spacing and layout

- Spacing tokens are named by pixels: `space-4` … `space-40`. Mobile screen padding: 20 px sides, 16 px top (`space-20`, `space-16`); onboarding and auth: 24 px sides.
- Gaps between blocks on a screen: 12–14 px. Inside cards: 10 px between lines, padding 14 × 16.
- Desktop: sidebar 220–272 px, main area padding 24 px top, 40 px sides, 24 px between sections, cards in wrapping rows with 20 px gaps.
- Full grids and screen recipes: see the section Layout and screens.

### Shape

Radii grow with the element: `radius-badge` 9 · `radius-sm` 12 (40 px controls) · `radius-md` 14 (44–48 px controls, code cells) · `radius-lg` 16 (52 px buttons and inputs, banners) · `radius-xl` 18 (shopping list groups) · `radius-bubble` 20 · `radius-card` 22 (cards) · `radius-card-lg` 24 (desktop cards) · `radius-hero` 28 (hero card, sheets) · `radius-pill` (round buttons, chips, tabs, avatars). Do not use sharp corners anywhere.

### Elevation

Flat. Cards are separated from `bg` by colour alone. The only shadows: `shadow-tab` under a selected segment and `shadow-sheet` under bottom sheets and dialogs, which sit on the `overlay` scrim.

### Imagery

- The fridge mascot (a friendly fridge character, closed and open versions) appears on login, the colour picker preview, the home hero card, the fridge screen header, and the desktop sidebar fridge card. Use the real illustrations from the canvas (asset group Mascot); never redraw it, never replace it with emoji or stock art.
- Food photos appear only on recipes (journal cards, AI idea card on desktop home), cropped `object-fit: cover` with 14 px or card radius. AI-generated photos carry the label «Згенеровано AI».
- No illustrations, gradients or patterns in the UI beyond these.

### Iconography

Inline SVG stroke icons only — 24 × 24 viewBox, stroke 2, round caps and joins, `currentColor`. The full set and its path data is in the Icons component. No emoji, no icon fonts.

### States

The design draws resting and selected states only. Add the others consistently (intentional additions):
- Focus: 2 px `accent` outline with 2 px offset on every interactive element (`:focus-visible`).
- Pressed: no colour change; the action responds immediately (optimistic update) and offers «Скасувати» in a toast where it changes data.
- Disabled buttons: `neutral-tile` fill, `text-subtle` text. Prefer an explanation to a disabled button.
- Loading: keep the layout; show skeleton blocks in `soft` with card radii. In AI Chef, a typing indicator in an AI bubble.
- Empty: a short sentence and one action, e.g. «У холодильнику поки порожньо» + «Додати продукт»; the mascot can appear here.
- Error: a sentence in plain Ukrainian next to the place it happened, `danger` text, never a red full-screen state.

### Motion

The design has no motion. Keep it minimal: 150–200 ms ease-out for sheets sliding up, tab and switch changes, and toasts; nothing decorative. Respect `prefers-reduced-motion` by removing movement.

## How to apply this in code

- Load the compiled tokens as CSS custom properties: each token becomes `--<name>` (`--accent`, `--radius-card`, `--space-16`, `--font-display`), each type style a class of its name (`.h1`, `.body-strong`). Theme ids are set on `<html data-theme="…">`; for the 9 palette colours without a theme block, compute the five themed values at runtime with the formula in Theming and write them on `:root`.
- Use `components/bundle.css` as the starting stylesheet; in React, build components that output exactly these class names and structures.
- Keep one source of truth: if a value is missing, add a token rather than hard-coding it.

## Do and don't

| Do | Don't |
| --- | --- |
| White cards on the tinted `bg` | Borders or shadows on cards |
| One full-width primary button per screen | Two accent buttons side by side |
| «до завтра», «2 дні», «у нормі» with colour | Colour dots or bars without words |
| Category colours only for categories | Category colours as decoration |
| `danger` text for «Вийти», «Видалити» | Red filled buttons, red banners |
| Theme tokens for tinted areas | The green `#3F6B4A` from older boards |
| Rubik for headings and numbers | Any third font, all caps, italics |
| Mascot from the asset files | Emoji, stock photos, a redrawn fridge |
