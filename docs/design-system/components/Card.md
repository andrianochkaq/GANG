# Card

White `surface` blocks with `radius-card` (22 px) on the tinted `bg` — the basic unit of every screen. No borders, no shadows.

- **Content card** (`fc-card`): padding 14 × 16, gap 10. Header row = title (Rubik 16 / 600) left + `fc-link` right («Усі», «Змінити»).
- **Hero card** (`fc-card--hero`): `soft` fill, `radius-hero`; one per screen — the home fridge card with mascot, stats and «Відкрити».
- **Link card**: a whole card as `<a>`: icon · title + meta · chevron right («Покупки · 2 списки»).
- **Desktop** (`fc-card--desktop`): `radius-card-lg`, padding 20 × 24, cards in a flex-wrap row with `space-20` gaps.
- Stack cards with `space-12` (`space-14` on roomier screens). Never nest a white card in a white card; inside a card use dividers or a `bg`/`soft` inset block.
- Stats inside cards: Rubik number (34 px mobile, 52 px desktop) over a 13 px label.

Design: [Main3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Main3) · [DHome](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DHome) · [Calories3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Calories3)
