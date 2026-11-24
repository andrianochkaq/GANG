# DataTable

Desktop lists (fridge products, calorie diary): a plain table inside a desktop card, header 13 / 600 `text-subtle`, rows divided by `divider`.

- Columns for the fridge: Продукт (600) · Категорія (`text-subtle`) · Кількість · Вжити до (Badge) · edit pencil (44 px ghost icon button with `aria-label`).
- Calorie diary: Страва · Прийом їжі · Ккал · Б / Ж / В, with a «Разом» row in 600 at the bottom.
- The card title says the sort order: «Усі продукти · спершу ті, що скоро зіпсуються».
- Wrap the table in `overflow-x:auto` with `min-width: 560px`; no zebra stripes, no vertical lines.

Design: [DFridge](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DFridge) · [DCalories](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DCalories)
