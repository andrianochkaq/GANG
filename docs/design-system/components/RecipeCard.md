# RecipeCard

A recipe suggested by AI Chef: white card with title + time/servings badge, an optional substitution warning, the ingredient list, and two actions.

- Title Rubik 18; badge «20 хв · 2 порції» right.
- If something is missing, a warning Banner comes first: what was replaced and «Смак буде трохи інший». Missing ingredients are marked in `status-soon-fg` («· немає») and can be added to the shopping list.
- Ingredient rows: name left, quantity 600 right. The «i» button (28 px `soft` circle, italic serif i) appears only when a verified conversion exists; it opens a dark `tooltip` popover: «5 г цукру ≈ 1 чайна ложка».
- Actions: primary «Я приготувала» / «Я приготував» (gendered from the profile; neutral «Страву приготовано» when gender is not set) and secondary «Інша ідея»; text action «Зберегти в щоденник».
- In the Recipe Journal the card adds a photo on top (AI-generated photos carry «Згенеровано AI»), meta «1 порція · 15 хв · 320 ккал» and «Усі продукти є вдома» (`ink`) or «Бракує: буряк, рукола» (`status-soon-fg`).

Design: [AI3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-AI3) · [Recipes](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Recipes) · [DAI](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DAI)
