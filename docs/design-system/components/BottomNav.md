# BottomNav

Mobile primary navigation: a 76 px white bar (`size-nav`) with a `line` top border and 3–4 equal items, icon over a 12 px label.

- Items, in this order: Холодильник · AI-кухар · Калорії (only when the calorie tracker is on) · Профіль. Nothing else goes here: shopping lists open from the home card, recipes from the profile.
- Active item: 56 × 30 px `soft` pill behind the icon, label in `ink` 600, `aria-current="page"`. Inactive: `text-subtle` 500.
- Icons are 22 px strokes: fridge, sparkle, bar chart, person.
- Hidden on onboarding, auth, sub-screens with a back button, and inside bottom sheets.
- `<nav aria-label="Основна навігація">`; on desktop it is replaced by the Sidebar.

Design: [Nav3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Nav3) · [Main3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Main3)
