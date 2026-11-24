# CategoryTile

The category view of the fridge: white tiles (`radius-bubble`, 16 px padding) with a 44 px coloured icon square, the category name and its count.

- Grid `repeat(auto-fill, minmax(150px, 1fr))`, gap `space-12`. On mobile: 2 columns.
- Icon square uses the fixed `cat-*-bg` fill and `cat-*-fg` icon colour — the same pair as the category chip.
- Tapping a tile filters the list below to that category; the selected tile gets a 2 px `accent` border (intentional addition).
- Categories with zero products are hidden.

Design: [DFridge](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DFridge) · [Fridge](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Fridge)
