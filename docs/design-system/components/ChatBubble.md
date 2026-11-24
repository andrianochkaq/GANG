# ChatBubble

AI Chef conversation: AI replies in white bubbles on the left, the user's messages in `accent` bubbles on the right, composer pinned at the bottom.

- AI bubble: `surface`, radius 20 with the bottom-left corner 6 px, max 300 px. User bubble: `accent` + `on-accent`, bottom-right corner 6 px, max 260 px. Text 15 px / 1.4.
- The first AI message of every conversation is exactly «Привітик! Що ти сьогодні хочеш поїсти?», followed by quick-reply chips.
- Recipes come as RecipeCards in the stream, not as bubbles.
- Composer: 52 px white pill (radius 26) with a `line` border, placeholder «Напишіть AI-кухарю…», 44 px `accent` round send button.
- Typing indicator (intentional addition): three 6 px `text-subtle` dots in an AI bubble.
- The AI addresses the user as «ти»; everything else in the UI uses «ви».

Design: [AI3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-AI3) · [DAI](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-DAI)
