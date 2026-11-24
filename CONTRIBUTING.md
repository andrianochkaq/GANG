# Contributing to FreeCook

## Branches

- `dev` is the integration branch. Start all work from `dev` and open
  pull requests into `dev`.
- `main` is for releases only. Do not base work on it, push to it or
  open pull requests against it. A person merges `dev` into `main` on
  GitHub and tags the release.
- Branch names follow `{type}/{2-3-word-summary}`, for example
  `feature/add-custom-user`. Do not put ticket numbers in branch names.

| Commit type                         | Branch prefix |
| ----------------------------------- | ------------- |
| `feat`                              | `feature/`    |
| `fix`                               | `bugfix/`     |
| `refactor`, `docs`, `test`, `ci`    | same as type  |
| `chore`, `build`, `perf`, `style`, `revert` | `chore/` |

The summary is the first two or three meaningful words of the commit
description.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

<body>

Refs #<issue number>
```

- Subject: at most 50 characters, imperative present tense, description
  starts in lowercase, no full stop, no ticket number.
- Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `ci`,
  `build`, `perf`, `style`, `revert`.
- Scopes: a Django app (`accounts`, `fridges`, `products`, `receipts`,
  `shopping`, `chef`, `nutrition`, `recipes`, `notifications`),
  `ui-<area>` for the frontend (`ui-auth`, `ui-fridge`, `ui-shopping`,
  `ui-chef`, `ui-calories`, `ui-profile`, `ui-recipes`, `ui-shell`,
  `ui-theme`), or `infra`, `ci`, `docs`, `deps`, `design`.
- Body: separated from the subject by a blank line, wrapped at 72
  characters, says what changed and why. Each paragraph starts with a
  capital letter.
- Breaking changes start a paragraph with `BREAKING CHANGE:`.
- The last line is `Refs #<issue number>`. This is the only place the
  issue number appears in a commit.

Example:

```
feat(accounts): add custom user model

Add a user model that logs in with email and keeps the theme colour.

Refs #17
```

## Pull requests and merging

- The pull request title is `#<issue number> <Description>` and the
  body contains `Closes #<issue number>`.
- Pull requests are squash-merged into `dev` after CI is green.
- Releases are tagged on `main` with SemVer and a `v` prefix, for
  example `v1.0.0` or `v1.0.0-rc.1`.

## Naming rules

Python and Django:

- Modules and packages: `lowercase_with_underscores`.
- Classes: `PascalCase` nouns without abbreviations; exceptions end in
  `Error`.
- Functions and variables: `snake_case`, functions start with a verb,
  no one-letter names.
- Constants and environment variables: `SCREAMING_SNAKE_CASE`.
- Django apps are plural (`fridges`), models are singular
  (`FridgeItem`), booleans start with `is_`, `has_` or `can_`.
- Tests live in `tests/test_<module>.py` and are named
  `test_<behaviour>`. URL paths are plural kebab-case
  (`/api/shopping-lists/`); JSON fields are `snake_case`.

TypeScript and React:

- Components: `PascalCase`, one per file, file named like the
  component. Presentational components use the `Base` prefix
  (`BaseButton`), single-use layout components use `The`
  (`TheBottomNav`).
- Functions and variables: `camelCase`, functions start with a verb,
  hooks are `useXxx`, booleans start with `is`, `has`, `should` or
  `can`.
- Constants: `SCREAMING_SNAKE_CASE`. Types: `PascalCase`, props are
  `<Component>Props`, no `I` prefix.
- Non-component files are `camelCase.ts`; folders are `kebab-case`.

## Secrets

Never commit passwords, tokens or keys. Read them from environment
variables and add only the variable name to `.env.example`.

## Tests

Every behaviour change comes with tests: pytest for the backend and
Vitest for frontend logic.
