# Chip

36 px pills (`size-chip`, `radius-pill`) for quick choices; 40 px pill tabs (`fc-tab`) for switching between lists.

- **Quick reply** (`fc-chip`): `surface` with a `line` border; AI Chef suggestions under the greeting («Сніданок», «Із того, що псується», «Щось солодке»). Tapping sends the text as the user's message.
- **Preset** (`fc-chip--neutral`, selected `fc-chip--selected`): one-of choices such as «Вжити до»: 3 дні / Тиждень / Місяць / Дата…. Selected = `accent` fill, `on-accent` text, 600.
- **Category** (`fc-chip--cat` + `--veg|--dairy|--meat|--fruit|--sweet|--other`): fixed category colours `cat-*-bg` / `cat-*-fg` — the only place where colour encodes a category. Selected adds a 2 px border in its own text colour. Never tint categories with the theme.
- **List tabs** (`fc-tabs` > `fc-tab`): shopping lists, «Усі / Від AI-кухаря / Власні» filters. Selected = `accent`. Label carries the count: «На тиждень · 3». «+ Новий» uses `fc-tab--new` (1 px dashed `dashed`).
- Use `aria-pressed` for toggles, `role="tab"` + `aria-selected` for tabs. Chip rows wrap; tab rows scroll horizontally.

Design: [AI3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-AI3) · [AddProduct](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-AddProduct) · [Shopping3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Shopping3) · [Recipes](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Recipes)
