# Button

The main action of a screen is one full-width `fc-btn--primary` (52 px, `accent` fill, `on-accent` text, `radius-lg`) at the bottom of the content.

**Variants** (class `fc-btn` + one):
- `fc-btn--primary` — the one action the screen is for. At most one per screen or card («Увійти», «Додати в холодильник», «Списати 150 г», «Готово»).
- `fc-btn--secondary` — `surface` with a 1 px `border-input`: alternatives on a light ground («За номером телефону», «Інша ідея», unselected choices).
- `fc-btn--plain` — `surface`, no border, on `bg` or `soft` («Закрити», «Відхилити», «Змінити акаунт»).
- `fc-btn--tonal` — `soft` fill for a secondary action that should still feel branded («Перезняти», «Сканувати штрихкод»).
- `fc-btn--danger` — `danger` text on `surface` («Вийти»). Never a red filled button.
- `fc-btn--text` — no fill («Додати й ще один», «Назад до реєстрації»).

**Sizes:** default 52 px (`radius-lg`, 16 px text) · `--md` 48 px (15 px) · `--sm` 44 px (`radius-md`, 14 px) · `--xs` 36 px (`radius-sm`, 13 px, only inside cards). Add `--block` for full width.

**Rules**
- Label = verb in the infinitive + object, sentence case, no full stop: «Додати продукт», «Перенести куплене в холодильник». Put the amount in the label when it matters: «Списати 150 г», «Додати 5 продуктів».
- Two equal actions sit in a 2-column grid with `space-8` gap: primary left, secondary right («Я приготувала» · «Інша ідея»; «Підтвердити» · «Відхилити»).
- On desktop, dialog buttons go right; destructive text action goes left.
- Icons: 18 px stroke icon before the label, `space-8` gap.
- Disabled (not in the design; intentional addition): `neutral-tile` fill, `text-subtle` text. Prefer explaining why an action is unavailable over disabling it.
- Use `<button>` for actions and `<a>` for navigation, both with this class.

Design: [Login3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Login3) · [Fridge3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Fridge3) · [AI3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-AI3) · [WriteOff3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-WriteOff3) · [DFridge](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DFridge)
