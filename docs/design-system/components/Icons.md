# Icons

All icons are inline SVG strokes on a 24 × 24 viewBox: `fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`; plus and minus use stroke 2.5.

- Sizes: 16 (badges, pills), 18 (buttons, banners), 20 (icon buttons), 22 (navigation, tiles), 24 (cards).
- Colour comes from `currentColor`: set it with the text colour token of the element.
- Decorative icons get `aria-hidden="true"`; an icon-only control gets `aria-label` on the control.
- Never use emoji, icon fonts or filled glyph sets. Do not mix in other libraries; when a new icon is needed, draw it in the same stroke style.

Path data for every icon:

- `fridge`: `<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M5 10h14M9 6v2M9 13v3"/>`
- `ai`: `<path d="M12 3l1.8 4.7 4.7 1.8-4.7 1.8L12 16l-1.8-4.7-4.7-1.8 4.7-1.8z"/><path d="M19 15l.7 1.8 1.8.7-1.8.7L19 20l-.7-1.8-1.8-.7 1.8-.7z"/>`
- `calories`: `<path d="M5 20V11M11 20V5M17 20v-7M3 20h18"/>`
- `profile`: `<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>`
- `back`: `<path d="M15 6l-6 6 6 6"/>`
- `chevron-right`: `<path d="M9 6l6 6-6 6"/>`
- `chevron-down`: `<path d="M6 9l6 6 6-6"/>`
- `plus`: `<path d="M12 5v14M5 12h14"/>`
- `minus`: `<path d="M5 12h14"/>`
- `trash`: `<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>`
- `pencil`: `<path d="M4 20h4L19 9l-4-4L4 16z"/>`
- `receipt`: `<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>`
- `cart`: `<circle cx="9" cy="20" r="1.5"/><circle cx="18" cy="20" r="1.5"/><path d="M2 3h3l2.5 12h12l2-8H6.2"/>`
- `water`: `<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>`
- `settings`: `<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>`
- `bell`: `<path d="M6 16V11a6 6 0 0 1 12 0v5l2 2H4z"/><path d="M10 21h4"/>`
- `phone`: `<rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/>`
- `telegram`: `<path d="M22 3L2 11l7 3 3 7z"/><path d="M9 14l13-11"/>`
- `barcode`: `<path d="M3 7V4h3M18 4h3v3M21 17v3h-3M6 20H3v-3M7 8v8M10 8v8M13 8v8M16 8v8"/>`
- `warning`: `<path d="M12 3l10 18H2z"/><path d="M12 10v4M12 17h.01"/>`
- `search`: `<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>`
- `send`: `<path d="M12 19V5M5 12l7-7 7 7"/>`
- `home`: `<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>`
- `veg`: `<path d="M5 19c0-8 6-14 14-14 0 8-6 14-14 14z"/><path d="M5 19l8-8"/>`
- `dairy`: `<path d="M10 2h4v4l2 3v12a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V9l2-3z"/><path d="M8 13h8"/>`
- `egg`: `<path d="M12 3c-4 0-7 6-7 11a7 7 0 0 0 14 0c0-5-3-11-7-11z"/>`
- `fruit`: `<path d="M12 7c-3-2-8-1-8 5 0 5 3 9 5 9 1 0 2-1 3-1s2 1 3 1c2 0 5-4 5-9 0-6-5-7-8-5z"/><path d="M12 7c0-2 1-4 3-4"/>`
- `sweet`: `<path d="M4 21h16v-8H4z"/><path d="M4 16c2 1 4 1 6 0s4-1 6 0 3 1 4 0"/><path d="M12 13V8"/>`
- `other`: `<path d="M5 21V11a3 3 0 0 1-1-5c1-2 4-3 8-3s7 1 8 3a3 3 0 0 1-1 5v10z"/>`

Design: [Nav3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Nav3) · [DSide](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DSide) · [DFridge](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DFridge)
