# TextField

A visible label (14 px / 600) above a 52 px white input with a 1 px `border-input` and `radius-lg`; focus turns the border into 2 px `accent`.

- Structure: `fc-field` > `fc-field__label` + `fc-input`. Gap `space-6` between label and input, `space-12` between fields.
- A helper link on the label row goes right (`fc-field__top` + `fc-field__link`): «Забули пароль?».
- Compact `fc-input--md` (48 px, `radius-md`) inside cards and next to a unit select (`fc-select`, 64 px wide: г / кг / мл / л / шт).
- Search (`fc-search`): 52 px, `line` border, search icon left, visually hidden label. Suggestions appear from the first letter.
- Placeholders are examples, never labels: «Наприклад, сир твердий», «Додати товар…», «Напишіть AI-кухарю…».
- Error (intentional addition): `aria-invalid="true"` = 2 px `danger` border and a `fc-field__error` line under the input in plain Ukrainian («Код неправильний. Спробуйте ще раз.»).
- Input text is 16 px so mobile browsers do not zoom.
- Number fields use `inputmode="numeric"`; email `type="email"`; phone fields keep the country code as a separate button.

Design: [Login3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Login3) · [AddProduct](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-AddProduct) · [Shopping3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Shopping3) · [DFridge](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DFridge)
