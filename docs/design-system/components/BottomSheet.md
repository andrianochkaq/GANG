# BottomSheet

Questions and short forms slide up from the bottom over an `overlay` scrim: white, top corners `radius-hero`, `shadow-sheet`, 40 × 5 px handle.

- Content order: kicker (13 / 600 `ink`, what just happened) → title (Rubik 24, a question) → one sentence of context → choices → one primary button → optional «Більше не питати…» checkbox.
- Choice groups (`fc-choice`): 3 equal 52 px buttons; selected = 2 px `accent` border on `soft`. Used for Так / Ні / Частково.
- The primary button repeats the exact result: «Списати 150 г».
- Use sheets for: write-off after logging food, «Ви це готували?», new shopping list, product quick edit. Close by swipe down, tap on scrim, or Esc.
- Desktop: the same content as a centred dialog (max 480 px wide, `radius-card-lg`) or a right side panel for lists.
- `role="dialog"`, `aria-label`, focus moves into the sheet and returns on close.

Design: [WriteOff3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-WriteOff3) · [Cooked3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Cooked3) · [NewList](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-NewList) · [DNewList](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DNewList) · [DShopping](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DShopping)
