# Stepper

−/+ buttons around a quantity: 40 px `soft` squares (`radius-sm`) in product rows, 48 px white squares with an editable value in write-off sheets.

- Step by a sensible unit: 1 for шт, 50 г / 50 мл for weight and volume (the label says it: «Більше на 50 г»).
- The value shows number + unit with a space: «400 г», «6 шт».
- Under an editable stepper, say the result: «Після списання в холодильнику залишиться 250 г.»
- Never go below 0; reaching 0 in the fridge asks to remove the product.
- `aria-label` includes the product: «Зменшити кількість: Йогурт грецький».

Design: [Fridge3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Fridge3) · [WriteOff3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-WriteOff3)
