# SegmentedControl

Two or three equal options on a `soft` track (`radius-lg`, `space-4` padding); the selected one is a white `surface` pill with `shadow-tab` and 600 weight.

- Use for switching views of the same content (Вхід / Реєстрація, Усі / Використайте першими) with `role="tablist"`, or for a setting choice (Вручну / За вагою) with `role="radiogroup"`.
- 40 px items by default; `--lg` 44 px on auth screens. Counts go in the label: «Усі · 12».
- `--neutral` uses `neutral-tile` for the track on settings cards that sit on white.
- Never more than 3 options; for more, use chips or list tabs.

Design: [Login3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Login3) · [Fridge3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Fridge3) · [Water](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Water)
