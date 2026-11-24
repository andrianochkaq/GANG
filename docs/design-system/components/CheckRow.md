# CheckRow

A 54 px tappable row with a 22 px native checkbox (`accent-color: accent`), the item name (16 px) and the quantity right (`text-muted`).

- The whole row is the `<label>`, so the touch target is the full row.
- Checked items move to a «Куплено · N» group below and are crossed out in `text-muted`.
- Group labels above each list: `fc-grouplabel` with the count («Треба купити · 3»).
- Also used for receipt review lines (checked by default; a doubtful line has its meta in `status-soon-fg` 600 — «Перевірте назву»).
- Lists live in `fc-list--tight` (`radius-xl`, rows divided by `divider`).

Design: [Shopping3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Shopping3) · [Receipt3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Receipt3)
