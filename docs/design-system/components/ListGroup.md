# ListGroup

A white `fc-list` card (`radius-card`) holding 56 px rows divided by 1 px `divider`; the standard way to show settings, navigation and people.

- Row anatomy (`fc-listrow`): main column (title 15 / 600 + optional meta 12 px `text-muted`) · trailing element: value text, `fc-link`, badge, switch, swatch, chevron or ⋯ button.
- Put a `fc-grouplabel` above each group («Функції — вмикайте, що потрібно», «Холодильники», «Користуються холодильником · 3»).
- A navigating row is an `<a>` covering the whole row; a row with a switch keeps the title as a link to settings and the switch as its own button.
- Rows with switches or two-line meta use `--tall` (62 px).
- Destructive actions are not rows; put «Вийти» as a `fc-btn--danger` below the groups.

Design: [Profile3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Profile3) · [Invite3](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Invite3) · [Fridges](https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt#artboard-Fridges)
