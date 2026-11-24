# Progress

Three shapes: a 6 px step bar (`line` track, `accent` fill), 8 px macro bars (`bg` track), and a 116 px calorie ring (12 px stroke).

- **Step bar** under «Реєстрація · крок N з 3» on onboarding screens.
- **Macro bars**: name 600 + «88 / 110 г» in `text-muted`, status word right — «у нормі» in `ink`, «замало» / «забагато» in `status-soon-fg`. Below-goal bars use `macro-low`. The word carries the meaning; the colour only repeats it.
- **Ring**: track `bg`, value `accent`, round caps, starts at 12 o’clock. Centre: number in Rubik 24 («1 240», non-breaking thin space for thousands) and «з 1 800 ккал». Right of it: «Залишилось», the remainder, and a status badge.
- **Water** uses the same bar at 12 px in `water-fill` on white inside the `water-bg` card.
- Give rings `role="img"` and an `aria-label` with the percentage.

Design: [Code3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Code3) · [Calories3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Calories3) · [Water](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Water) · [DCalories](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DCalories)
