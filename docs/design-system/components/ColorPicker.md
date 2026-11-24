# ColorPicker

The app-colour picker: 17 named swatches in a 6-column grid, each a 46 px ring around a colour dot with the name under it (12 px).

- Order and names are fixed: Білий, Океан, Небо, Бузок, Лаванда, Смарагд, Літо, Паросток, Лайм, Кориця, Захід, Персик, Лимон, Бургунді, Вишня, Сакура, Туман (tokens `swatch-*`).
- Selected = 2 px `text` ring. `role="radiogroup"` / `role="radio"` with `aria-checked`; `aria-label` = colour name.
- Above the grid show a live preview card (mascot on `soft`, two `soft` text bars, an `accent` «Кнопка») and «Обрано: <b>Сакура</b>».
- Choosing a colour recolours the whole app at once (see Theming). Default is Білий. Under the main button: «Колір можна змінити в профілі.»
- In onboarding it is step 3 of 3 with the button «Готово».

Design: [Color3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Color3) · [DColor](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DColor)
