# Theming

The user picks one of 17 app colours (default Білий); five tokens — `bg`, `soft`, `line`, `accent`, `ink` — are derived from it and recolour the whole app. All other colours stay fixed.

## Rules

- Apply the theme to every screen, including auth after login, sheets, sidebar and navigation. Never tint only the accent and leave a neutral page: the tinted `bg` is part of the brand.
- Derived values only. Never paint a surface with the raw swatch colour (`swatch-*`): Сакура `#f2cedb` as a page background fails text contrast; its `bg` `#fdf8fa` does not.
- Text colours (`text`, `text-secondary`, `text-muted`, `text-subtle`) never change with the theme. White text appears only on `accent`, `water-fill` and `tooltip`.
- The theme is per user and follows them across devices and fridges. It can be changed in Профіль › Колір застосунку; the change is instant, no Save button.
- `tokens.json` carries 8 of the themes so the design-system page can preview them: Білий (`white`, first and default), Сакура, Океан, Літо, Захід, Смарагд, Лаванда, Вишня. The other 9 come from the formula below at runtime with the same results.

## The formula

From the chosen hex `c`:

| Token | Value |
| --- | --- |
| `bg` | `mix(c, white, 0.86)` |
| `soft` | `mix(c, white, 0.60)` |
| `line` | `mix(c, white, 0.50)` |
| `accent` | `c`, darkened by `mix(a, black, 0.10)` repeatedly until the contrast of `#ffffff` on it is at least 4.8:1 (max 30 steps) |
| `ink` | `mix(accent, black, 0.30)` |

Білий is special: `bg #f7f5f0`, `soft #ece8e0`, `line #e4dfd5`, `accent #2f2e2b`, `ink #2f2e2b`.

```js
function mix(hex, to, t) {            // to: 255 = white, 0 = black
  const c = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16));
  return '#' + c.map(v => Math.round(v + (to - v) * t).toString(16).padStart(2, '0')).join('');
}
function lum(hex) {
  return [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map(v => v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4))
    .reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0);
}
function contrast(a, b) { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
function theme(hex) {
  const h = hex.toUpperCase();
  if (h === '#FFFFFF') return { bg: '#f7f5f0', soft: '#ece8e0', line: '#e4dfd5', accent: '#2f2e2b', ink: '#2f2e2b' };
  let a = h, i = 0;
  while (contrast(a, '#FFFFFF') < 4.8 && i < 30) { a = mix(a, 0, 0.1); i++; }
  return { bg: mix(h, 255, 0.86), soft: mix(h, 255, 0.6), line: mix(h, 255, 0.5), accent: a, ink: mix(a, 0, 0.3) };
}
// apply: Object.entries(theme(hex)).forEach(([k, v]) => document.documentElement.style.setProperty('--' + k, v));
```

Run the same function on the server or in a unit test to check the table below; every theme keeps `text` and `text-subtle` at 4.5:1 or better on `bg`, and `ink` on `soft`.

## All 17 themes

| Swatch | Name | bg | soft | line | accent | ink |
| --- | --- | --- | --- | --- | --- | --- |
| `#ffffff` | Білий (`white`) | `#f7f5f0` | `#ece8e0` | `#e4dfd5` | `#2f2e2b` | `#2f2e2b` |
| `#6387bd` | Океан (`ocean`) | `#e9eef6` | `#c1cfe5` | `#b1c3de` | `#506e99` | `#384d6b` |
| `#a9d4ef` | Небо (`sky`) | `#f3f9fd` | `#ddeef9` | `#d4eaf7` | `#5a7180` | `#3f4f5a` |
| `#d8bce3` | Бузок (`lilac`) | `#faf6fb` | `#efe4f4` | `#ecdef1` | `#736479` | `#504655` |
| `#b0a3cf` | Лаванда (`lavender`) | `#f4f2f8` | `#dfdaec` | `#d8d1e7` | `#736b87` | `#504b5e` |
| `#4a6a50` | Смарагд (`emerald`) | `#e6eae6` | `#b7c3b9` | `#a4b4a8` | `#4a6a50` | `#344a38` |
| `#8db07e` | Літо (`summer`) | `#eff4ed` | `#d1dfcb` | `#c6d8be` | `#5d7353` | `#41503a` |
| `#dce5bc` | Паросток (`sprout`) | `#fafbf6` | `#f1f5e4` | `#eef2de` | `#696d5a` | `#4a4c3f` |
| `#d4e157` | Лайм (`lime`) | `#f9fbe7` | `#eef3bc` | `#eaf0ab` | `#666c29` | `#474c1d` |
| `#a66e44` | Кориця (`cinnamon`) | `#f3ebe5` | `#dbc5b4` | `#d2b6a2` | `#95633d` | `#68452b` |
| `#f0b95e` | Захід (`sunset`) | `#fdf5e8` | `#f9e3bf` | `#f8dcae` | `#806232` | `#5a4523` |
| `#f6df8a` | Персик (`peach`) | `#fefbef` | `#fbf2d0` | `#faefc4` | `#756b43` | `#524b2f` |
| `#fff97f` | Лимон (`lemon`) | `#fffeed` | `#fffdcc` | `#fffcbf` | `#6e6c37` | `#4d4c26` |
| `#b0334a` | Бургунді (`burgundy`) | `#f4e2e6` | `#dfadb7` | `#d899a4` | `#b0334a` | `#7b2434` |
| `#e07a70` | Вишня (`cherry`) | `#fbeceb` | `#f3cac6` | `#f0bcb8` | `#a45952` | `#733e39` |
| `#f2cedb` | Сакура (`sakura`) | `#fdf8fa` | `#faebf1` | `#f8e6ed` | `#806d74` | `#5a4c51` |
| `#c8c8c8` | Туман (`fog`) | `#f7f7f7` | `#e9e9e9` | `#e4e4e4` | `#6a6a6a` | `#4a4a4a` |

## Where each themed token appears

- `bg`: page background of every screen, track of macro bars and the calorie ring, background of the partial write-off box.
- `soft`: home hero card, segmented-control track, info badges, stepper buttons, «i» hint, avatar on profile, active nav pill and sidebar item, selected choice button, tip banners, colour-picker preview.
- `line`: onboarding progress track, quick-reply chip outline, chat composer border, nav top border, search field border.
- `accent`: primary buttons, send and add icon buttons, user chat bubble, active list tab, selected preset chip, switches on, checkboxes, progress fills, focus ring, selected choice border.
- `ink`: inline links, active nav and sidebar label, «у нормі», sheet kicker, «Усі продукти є вдома».
