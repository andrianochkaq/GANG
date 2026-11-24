# Naming conventions

Rules for every name in this repository. Git, Python and JavaScript rules follow https://namingconvention.org (Git, Python and VueJS sections; the VueJS rules are applied to React). Lines marked **[project]** are FreeCook decisions where the site is silent or two of its rules clash. CI checks branch names, PR titles, PR targets and commit messages on every pull request (`conventions` job).

## Git

### Branch model

- `dev` is the integration branch: every feature branch starts from `dev` and every PR targets `dev`.
- `main` holds releases only. Automation (the AI, `fc.sh`) never checks out, pulls, pushes, merges or opens PRs against `main`. A release is a PR from `dev` into `main`, opened and merged by a person on GitHub.

### Branches

Format: `{type}/{2-3-word-summary}` — e.g. `feature/add-custom-user`

- **[project]** Nobody types branch names. `fc.sh` generates them when it applies a patch: the type comes from the first commit's type (table below), the summary from the first 2–3 meaningful words of its description ("feat(accounts): add custom user model" → `feature/add-custom-user`). Small words (the, a, to, for, of, and, with, in, on, from, into, by) are skipped; on a clash, another word from the description is used.
- Summary: 2–3 words, imperative present tense, lowercase, words separated by hyphens.
- Type, one of: `feature`, `bugfix`, `hotfix`, `refactor`; **[project]** also `chore`, `docs`, `test`, `ci` so every commit type has a branch type.
- **[project]** No ticket numbers in branch names. The issue is linked from the commit footer and the PR title.
- **[project]** Patch files are named after the GitHub issue: `17.patch`, then `17--fix-1.patch`, `17--fix-2.patch` for follow-ups. A task with no issue: `task-<short-slug>.patch`. `fc.sh` sends follow-ups to the branch of the open PR for that issue.

| Branch type | Use for | Commit type |
| --- | --- | --- |
| `feature` | New behaviour from a ticket | `feat` |
| `bugfix` | A bug found during development (generated from `fix`) | `fix` |
| `hotfix` | An urgent fix for production (only when named by a person) | `fix` |
| `refactor` | Restructuring with no behaviour change | `refactor` |
| `chore` | Tooling, dependencies, housekeeping | `chore`, `build`, `perf`, `style`, `revert` |
| `docs` | Documentation only | `docs` |
| `test` | Tests only | `test` |
| `ci` | CI/CD workflows | `ci` |

### Commit messages

Conventional Commits format: `<type>(<scope>): <description>`

```
feat(accounts): add custom user model

Users can now sign up by email, phone or Telegram. Every account
needs at least one of the three, enforced by a database constraint.

Refs #17
```

Subject:
- At most 50 characters in total, imperative present tense, no full stop at the end.
- **[project]** No ticket numbers (no `FC-101`, no `#17`) in the subject.
- Types: `feat`, `fix`, `docs`, `chore` (named on the site) and, from Conventional Commits, `refactor`, `test`, `ci`, `build`, `perf`, `style`, `revert`.
- **[project]** The description starts lowercase, as in the site's Conventional Commits example (`feat(survey): add nps survey to the home page`). This replaces the plain-subject rule "capitalized".
- **[project]** Scope = the area changed: a Django app (`accounts`, `fridges`, `products`, `receipts`, `shopping`, `chef`, `nutrition`, `recipes`, `notifications`), a frontend area prefixed `ui-` (`ui-auth`, `ui-fridge`, `ui-shopping`, `ui-chef`, `ui-calories`, `ui-profile`, `ui-recipes`, `ui-shell`, `ui-theme`), or `infra`, `ci`, `docs`, `deps`, `design`.

Body (optional):
- Separated from the subject by a blank line; lines wrapped at 72 characters.
- Explains what changed and why; each paragraph starts with a capital letter.
- Breaking changes start the body or footer with `BREAKING CHANGE: ` (or `!` after the type/scope).
- **[project]** Footer `Refs #<issue>` links the GitHub issue (the only place a number appears in a commit). The PR closes the issue, not the commit.

### Pull requests

- Base branch: always `dev`. (Only the release PR `dev` → `main` targets `main`, made by a person.)
- Title: `#{ticket} {Description}` — e.g. `#17 Add custom user model`, where the ticket id is the GitHub issue number. Capitalized, imperative present, no full stop, brief. Without an issue: just `Add custom user model`.
- Description: blank line after the title; what the PR changes and why plus context for the reviewer; paragraphs start with a capital; lines wrapped at 72 characters. The template adds `Closes #<issue>` and the test checklist.
- **[project]** PRs are squash-merged into `dev`; the squash commit takes the Conventional Commit subject of the branch's first commit plus `(#<PR number>)`.

### Tags

- Semantic Versioning `MAJOR.MINOR.PATCH` with the `v` prefix: `v1.0.0`, `v1.2.3`.
- **[project]** Pre-releases use SemVer labels: `v1.0.0-rc.1`. Annotated tags on `main` after a release merge: `git tag -a v1.0.0 -m "v1.0.0"`. A pushed `v*` tag triggers the deploy workflow.

## Python / Django

| Thing | Style | Examples |
| --- | --- | --- |
| Packages, modules, files | lowercase, words joined by `_`, named after what they contain | `fridges`, `stock_service.py`, `test_invites.py` |
| Classes | PascalCase noun, no acronyms or abbreviations | `FridgeItem`, `ShoppingList`, `OneTimeCode` |
| Private classes | leading `_` + class rules | `_CodeHasher` |
| Exceptions | PascalCase, `Error` suffix when it is an error | `InviteExpiredError`, `UnitConversionError` |
| Functions, methods | lowercase snake_case, start with a verb | `issue_code()`, `consume_item()`, `get_use_first()` |
| Private functions, methods | leading `_` | `_hash_code()` |
| Variables, arguments | lowercase snake_case; no one-letter names; never start with a special character | `fridge_item`, `max_uses` |
| Constants | SCREAMING_SNAKE_CASE, may contain digits but not start with one | `CODE_TTL_MINUTES`, `MAX_LOGIN_ATTEMPTS` |

Underscores:
- `_` alone for values you ignore: `for _ in range(3)`, `name, _ = split_name(full)`.
- `_single_leading` for internal names (skipped by `from module import *`).
- `single_trailing_` to avoid a keyword or built-in: `type_`, `id_`, `class_`.
- `__double_leading` only when name mangling is really needed.
- `__dunder__` only for Python's special methods; never invent new ones.

**[project]** Django specifics:
- Apps: plural lowercase (`fridges`, `recipes`). Models: singular PascalCase noun (`Fridge`, `RecipeStep`). Fields: snake_case; booleans start with `is_`, `has_` or `can_` (`is_bought`, `is_email_verified`).
- Serializers, views, permissions end with their role: `FridgeItemSerializer`, `FridgeItemViewSet`, `IsFridgeMember`.
- Celery tasks: verb-first snake_case (`send_email_code`, `parse_receipt`). Services: modules in `services/`, functions verb-first.
- Tests: `tests/test_<module>.py`, functions `test_<behaviour>` (`test_third_join_is_refused`).
- API: URL paths plural nouns in kebab-case (`/api/fridges/{id}/use-first/`, `/api/shopping-lists/`); JSON fields snake_case.
- Environment variables: SCREAMING_SNAKE_CASE (`DJANGO_SECRET_KEY`, `VITE_API_URL`).

## TypeScript / React

Rules from the site's VueJS section, applied to React:

| Thing | Style | Examples |
| --- | --- | --- |
| Components | PascalCase, multi-word, no acronyms or abbreviations | `ProductCard`, `FridgeSwitcher` (not `Card`, `ProdCrd`) |
| Child components | prefixed with the parent's name | `RecipeCardIngredient` inside `RecipeCard` |
| Presentational ("dumb") components | `Base` prefix; look and feel only | `BaseButton`, `BaseTextField`, `BaseBadge` |
| Container ("smart") components | the base name with a meaningful prefix instead; hold logic and data | `WriteOffButton`, `SubmitButton` (wrap `BaseButton`) |
| Components used once per view | `The` prefix | `TheBottomNav`, `TheSidebar`, `TheAppShell` |
| Component files | PascalCase, one component per file, `.tsx` | `ProductCard.tsx`, `TheBottomNav.tsx` |
| JSX | PascalCase tags; self-closing when there are no children | `<ProductCard item={item} />` |
| Functions, methods | camelCase, start with a lowercase verb | `addProduct()`, `getUseFirst()` |
| Variables | camelCase; no `_` or `-`; no one-letter names; never start with a digit | `activeFridgeId`, `phoneNumber` |
| Constants | SCREAMING_SNAKE_CASE; digits allowed, not first | `MAX_INVITE_USES`, `RESEND_DELAY_SECONDS` |

**[project]** React specifics:
- Design-system components become `Base*` components: Button → `BaseButton`, TextField → `BaseTextField`, Chip → `BaseChip`, Card → `BaseCard`; single-instance ones take `The`: BottomNav → `TheBottomNav`, Sidebar → `TheSidebar`. They render the `fc-*` classes from `docs/design-system/components.css`.
- Hooks: `use` + PascalCase (`useActiveFridge`). Event handler props `on<Event>` (`onConfirm`); handler functions `handle<Event>` (`handleConfirm`).
- Booleans start with `is`, `has`, `should` or `can` (`isLoading`, `hasCalories`).
- Types and interfaces: PascalCase nouns, props `<Component>Props` (`ProductCardProps`); no `I` prefix.
- Non-component modules: camelCase file names (`apiClient.ts`, `themes.ts`); folders lowercase kebab-case (`features/shopping-lists/`).
- i18n keys: dot-separated camelCase by feature (`fridge.addProduct`, `auth.forgotPassword`).
- CSS classes: the design system's `fc-block__element--modifier` pattern only.

## When a ticket's file name breaks these rules

These conventions win. Use the conforming name (e.g. `TheAppShell.tsx` instead of `AppShell.tsx`) and mention the rename in the PR description.
