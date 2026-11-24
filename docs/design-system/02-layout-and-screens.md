# Layout and screens

Every screen is built from the same few frames and components. Pick the frame, then follow the screen recipe; the linked board shows the exact composition.

Canvas: https://claude.ai/artifact/7FyeB4mxzjrVG7urEWgPmt (add `#artboard-<Name>` to open one board).

## Frames

### Mobile (design width 390 px, `size-phone`)

- **Tab root** (Холодильник home, AI-кухар, Калорії, Профіль): `bg`, padding 16 px top / 20 px sides, content column with 12–14 px gaps, BottomNav (76 px) pinned at the bottom. Header = title or wordmark + actions.
- **Sub-screen** (add product, receipt, water, recipes, members, edit profile, shopping): back IconButton + title 22 + subtitle; no BottomNav, except Shopping, which keeps it. Primary button pinned to the bottom with `margin-top: auto`.
- **Onboarding / auth** (login, phone, code, forgot password, colour): padding 24 px; step label + progress bar; h1 28 + explanation; form; primary button; supporting box or legal line at the bottom. No nav.
- **Bottom sheet** over the current screen for questions and short forms.

### Desktop (design width 1440 px, `size-desktop`)

- Sidebar (220–272 px, `sidebar`) + main area (`bg`, padding 24 px top / 40 px sides, 24 px between sections). The main area is fluid: cards sit in flex-wrap rows (`flex: 2 1 460px` for the main card, `flex: 1 1 300px` for side cards) with 20 px gaps.
- Page header: h1 32 + 15 px subtitle left; header actions right (water pill, notifications, avatar on home; «Закрити» + primary «Додати продукт» on the fridge).
- Auth on desktop: two halves — brand side with the mascot and a short explanation, form side with the form 400 px wide, centred.
- Lists open as a right side panel over the dimmed app; questions as centred dialogs (max 480 px) over `overlay`.

### Breakpoints (intentional addition: the design shows only 390 and 1440)

- Below 768 px: mobile frames with BottomNav.
- 768–1023 px: mobile frames, content centred with `max-width: 560px`.
- 1024 px and up: desktop frame with Sidebar.

## Screen recipes

Each line: frame · components in order · board.

### Auth and onboarding

- **Login and registration** — onboarding frame · mascot in a 132 px `soft` circle + «FreeCook» · SegmentedControl Вхід / Реєстрація · TextField email · TextField password with «Забули пароль?» · primary «Увійти» · divider «або без пароля» · secondary buttons «За номером телефону — код у SMS» and «Через Telegram — через бота» · legal line 12 px. Board: `Login3`, desktop `DLogin`.
- **Phone login** — back · title · country-code button + phone field · CodeInput on the same screen · note that phone accounts have no password and recovery is by email in the profile. Board: `Phone3`, `DPhone`.
- **Email code** — «Назад до реєстрації» · «Реєстрація · крок 2 з 3» + bar · h1 «Підтвердьте пошту» · CodeInput · primary «Підтвердити» · info box «Як працює реєстрація» with 3 numbered steps. Board: `Code3`.
- **Forgot password** — back · h1 · email field · primary · numbered steps of what happens next · buttons to log in by code instead. Board: `Forgot3`, `DForgot`.
- **App colour** — «Реєстрація · крок 3 з 3» · h1 «Колір застосунку» · preview card · ColorPicker · primary «Готово» · «Колір можна змінити в профілі.» Board: `Color3`, `DColor`.

### Fridge

- **Home** — tab root · header wordmark + WaterPill + avatar · h1 «Добрий ранок, Марто» + «Наш холодильник · 3 учасники» · FridgeCard · «Додати продукти»: two 64 px white buttons «Фото чека — AI все розпізнає» (2 px `accent` border) and «Вручну — назва і кількість» · card «Використайте першими» (2 rows + «Усі») · link card «Покупки · 2 списки». Board: `Main3`, `DHome`.
- **Fridge contents** — sub-screen with back «Закрити холодильник» · title «Що всередині» + «12 продуктів · бачать 3 учасники» + open-fridge mascot · search · category tiles (from `Fridge` / `DFridge`) · SegmentedControl «Усі · 12 / Використайте першими · 4» · list of ProductRows (desktop: DataTable) · bottom buttons «З чека» (primary) and «Вручну» (plain). Board: `Fridge3`, `Fridge`, `DFridge`.
- **Add product** — back + «Додати продукт / У «Наш холодильник»» · two 76 px buttons «Сканувати штрихкод» (tonal, optional feature) and «Фото чека» · divider «або вручну» · white card: name (active border), category chips, quantity + unit, «Вжити до» presets · primary «Додати в холодильник» · text «Додати й ще один». Board: `AddProduct`.
- **Edit product** — form in two columns on desktop; unit as a separate select; «Видалити» in `danger` left, «Зберегти» right; «Хто і коли додав»; link «Що приготувати з йогурту?». Board: `Edit`, `DEdit`.
- **Receipt review** — back + «Продукти з чека / Перевірте, що розпізнав AI» · receipt summary card (paper thumbnail, time, count, skipped non-food, «Перезняти») · CheckRows with quantity chips · warning Banner for unsure lines · primary «Додати 5 продуктів» + note that expiry dates are approximate. Board: `Receipt3`.
- **Write-off** — BottomSheet over the current screen: kicker, «Списати з холодильника?», Так / Ні / Частково, partial Stepper with the remainder sentence, primary «Списати 150 г», «Більше не питати для цього продукту». Board: `WriteOff3`.
- **Fridge list** — current fridge highlighted with a border and «поточний», members and products count per fridge, pencil to rename, «Новий холодильник». Board: `Fridges`, `DFridges`.

### Shopping

- **Lists** — sub-screen (keeps BottomNav) · back + «Покупки» + ⋯ · list tabs with counts + «+ Новий» · add-item field + 48 px accent «+» · «Треба купити · N» CheckRows · «Куплено · N» CheckRows · primary «Перенести куплене в холодильник». Desktop: side panel over the app. Board: `Shopping3`, `DShopping`.
- **New list** — BottomSheet / dialog: name field (active) and «Швидкий старт»: empty, from what is running out, copy of a previous list. Board: `NewList`, `DNewList`.

### AI Chef

- **Chat** — tab root · sparkle + «AI-кухар» · ChatBubbles (greeting «Привітик! Що ти сьогодні хочеш поїсти?») · quick-reply chips · RecipeCards in the stream · composer pinned above the BottomNav. Desktop adds a right column «Під рукою» (products with expiry) and more ideas. Board: `AI3`, `DAI`.
- **Did you cook this?** — BottomSheet: «Ви це готували?» → Так / Ні → write off all / partially. Board: `Cooked3`.

### Calories and water

- **Calories** — tab root (only when enabled) · title + settings IconButton · tip Banner «Ціль: схуднення · розраховано за вагою 65 кг — Змінити» · ring card · macro bars card · diary card with «+ Додати їжу». Desktop: diary as a table with «Разом». Board: `Calories3`, `DCalories`.
- **Calorie settings** — Вручну / За вагою і ціллю; weight, goal (скинути / тримати / набрати) → calculated kcal and macros. Board: `CalSettings3`.
- **Water** — sub-screen · `water-bg` card: total «1,2 л» + «з 2 л сьогодні», 12 px bar, quick buttons +150 / +250 (selected, `water-fill`) / +500 мл · settings card: «Показувати в шапці», goal Вручну / За вагою, weight select + «≈ 2 л на день» · «Сьогодні» log with times. Board: `Water`.

### Profile

- **Profile** — tab root · header card (avatar 52, name, email, edit pencil) · «Функції — вмикайте, що потрібно»: water switch row, calorie switch row, app colour row · «Холодильники»: current fridge, «Учасники і запрошення» with request badge, «Щоденник рецептів» with count · bottom 2-column «Змінити акаунт» / «Вийти» (`danger`). Desktop: sections menu left, content right; join request as a banner. Board: `Profile3`, `DProfile`.
- **Members and invitations** — back + «Учасники / Наш холодильник» · card «Нове запрошення»: how many people (select 1, 2, 3, 5), link + «Копіювати», «Використано 1 з 2» + «Після 2 людей посилання зміниться» · pending request card on `soft` (avatar 44, name, @nickname · time, «Підтвердити» / «Відхилити») · «Користуються холодильником · 3» list with «власниця» badge and ⋯ menus. Board: `Invite3`, `Members`.
- **Edit profile** — name, nickname for invitations, email, phone, password, gender. Board: `EditProfile`.
- **Recipe journal** — back + title + count + accent «+» · tabs Усі / Від AI-кухаря / Власні · recipe cards (photo, badge, meta, availability line) · tip Banner about adding missing items to shopping. Board: `Recipes`.

## Screens with no board

Build these from the nearest recipe and say so in your summary:
- Join by invitation link → Login3 layout with the fridge name, owner and «Приєднатися», then a waiting state.
- Notification settings → Profile3 list style with two switches (browser notifications, Telegram).
- Recipe editor → AddProduct form style; ingredients as rows with quantity + unit; steps as a numbered list.
- Delete account and export data → Profile3 list style; destructive actions in `danger` text with a confirmation sheet.
- Desktop versions of version 3 screens (code, receipt, write-off, cooked, calorie settings, invite, add product, water, recipes, edit profile) → centred dialog or right side panel like DNewList and DShopping.
