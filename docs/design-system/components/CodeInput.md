# CodeInput

Six 56 px cells (`size-code-cell`, `radius-md`) in a 6-column grid with `space-8` gaps for email and SMS codes.

- Wrap in a `fieldset` with a `legend` («Код із листа», «Код із SMS»). Each cell has `aria-label="Цифра N"` and `inputmode="numeric"`.
- Filled or focused cells get a 2 px `accent` border; empty cells 1 px `border-input`. Digits 22 px / 600.
- Typing moves focus to the next cell; paste of 6 digits fills all; Backspace goes back.
- Under the cells: resend timer and help in `text-subtle` 13 px — «Надіслати ще раз через 0:58 · перевірте «Спам»». When the timer ends, the time becomes a link «Надіслати ще раз».
- On the phone screen the cells appear right under the number, on the same screen.

Design: [Code3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Code3) · [Phone3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Phone3)
