# Agent checklist

Go through this list before you call a FreeCook screen done. Every item is a yes / no.

## Before you build

- [ ] I read README, Theming, Layout and screens, Content and voice, and the README of every component I use.
- [ ] I opened the screen's board on the canvas (version 3 for mobile, «Стало» for desktop) and know its recipe.
- [ ] I know which frame the screen uses: tab root, sub-screen, onboarding, bottom sheet, or desktop main area.

## Tokens and styling

- [ ] Every colour, radius, spacing, size and shadow is a token (`var(--name)`); no raw hex or px values that have a token.
- [ ] Themed areas use `bg`, `soft`, `line`, `accent`, `ink`; switching the theme recolours the whole screen.
- [ ] I used no colour from older boards (`#3F6B4A`, `#2F5E8C` as accent) and no new colours.
- [ ] Cards are `surface` on `bg` with `radius-card`, no borders or shadows.
- [ ] Headings and numbers are Rubik 600; all other text Inter 400 / 500 / 600 at the named type styles.

## Components and layout

- [ ] There is at most one `accent` primary action on the screen.
- [ ] Mobile: header row, content with 12–14 px gaps, 20 px side padding; BottomNav on tab roots only (plus Shopping).
- [ ] Desktop: Sidebar + main area with 24 / 40 px padding; dialogs and side panels instead of new pages for short tasks.
- [ ] The Calories tab appears only when the calorie tracker is on.
- [ ] Lists sort Use First items first; expiry badges use urgent / soon / ok by days left.

## Content

- [ ] All text is Ukrainian, sentence case, no emoji; buttons are infinitive verbs.
- [ ] UI uses «ви», AI Chef uses «ти»; gendered words follow the profile gender, neutral when unset.
- [ ] Numbers use decimal commas, non-breaking spaces in thousands, units after a space, correct plurals.
- [ ] Status is written in words, not shown by colour alone.

## Accessibility

- [ ] Every control is 44 px or more (40 px steppers and tabs only inside rows; 36 px chips only in chip rows).
- [ ] Every input has a visible label (or a visually hidden one for search and chat); every icon-only control has a Ukrainian `aria-label`.
- [ ] Switches, tabs, radio groups and dialogs carry their roles and states.
- [ ] Focus is visible (2 px `accent` outline) and follows a logical order; sheets trap and return focus.
- [ ] Text contrast pairs are the documented ones; nothing places `text-subtle` on `soft` or text on `accent`.

## States

- [ ] Loading (skeletons in `soft`), empty (sentence + one action), error (sentence near the cause, `danger` text) are designed for every list and form.
- [ ] Data changes are optimistic, with «Скасувати» where something is removed or written off.

## Report

- [ ] In your summary, name any screen or part built without a board and the recipe you followed, and any token you had to add.
