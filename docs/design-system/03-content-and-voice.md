# Content and voice

FreeCook talks like a helpful flatmate who cooks: short, warm, concrete. Every string is Ukrainian.

## Voice

- **Short and concrete.** Say the number and the thing: «12 продуктів», «2 скоро зіпсуються», «Залишилось 560 ккал».
- **Calm, never alarming.** No exclamation marks in the UI except the AI Chef greeting. No red alarms for food going off — «до завтра», not «ТЕРМІНОВО».
- **Explain consequences** in one sentence where an action changes data: «Після списання в холодильнику залишиться 250 г.», «Після 2 людей посилання зміниться».
- **Admit uncertainty** from AI plainly: «Розпізнано неточно. Натисніть, щоб уточнити назву.», «Терміни придатності AI підставив орієнтовно — їх можна змінити.»
- **No emoji, no slang, no English UI words** (except the names «FreeCook», «AI», «Telegram», «SMS»).

## Address

- The app speaks to the user with **«ви»** (lowercase): «Оберіть інший», «Скільки ви використали?», «Перевірте, що розпізнав AI».
- The **AI Chef speaks with «ти»** and is friendly: «Привітик! Що ти сьогодні хочеш поїсти?» is its fixed first message.
- **Gendered forms follow the user's gender from the profile**: «Я приготувала» / «Я приготував»; when gender is not set, use a neutral form: «Страву приготовано». Never write «приготував(ла)».
- Greet by first name in the vocative: «Добрий ранок, Марто». Time of day: «Добрий ранок» / «Добрий день» / «Добрий вечір» by the user's local time.

## Casing and punctuation

- Sentence case everywhere: «Додати продукт», «Використайте першими». No ALL CAPS, no Title Case.
- Buttons: verb in the infinitive + object, no full stop: «Увійти», «Додати в холодильник», «Перенести куплене в холодильник», «Списати 150 г». Short confirmations: «Готово», «Підтвердити», «Відхилити», «Скасувати».
- Titles of screens and cards: nouns or short phrases, no full stop: «Що всередині», «Покупки», «Щоденник рецептів».
- Questions in sheets end with «?»: «Списати з холодильника?», «Ви це готували?».
- Ukrainian quotes «…», apostrophe ’ (М’ясо, пам’ять), dash — with spaces, ellipsis … as one character.
- Separator between facts: middle dot with spaces « · »: «20 хв · 2 порції», «Наш холодильник · 3 учасники».

## Numbers, units, dates

- Decimal comma: «1,2 л», «2,5%». Thousands with a non-breaking space: «1 240 ккал».
- Units after a space, no dots: г, кг, мл, л, шт, ккал, хв. «≈» for approximations: «≈ 2 л на день», «5 г цукру ≈ 1 чайна ложка».
- Counts use correct Ukrainian plurals (`Intl.PluralRules('uk')`): 1 продукт / 2 продукти / 5 продуктів; 1 учасник / 3 учасники / 5 учасників; 1 день / 2 дні / 5 днів; 1 порція / 2 порції / 5 порцій; 1 запит / 2 запити / 5 запитів.
- Expiry labels: «прострочено», «сьогодні», «до завтра», then «2 дні», «5 днів»; on lists with dates: «до 28 листопада». Month names in the genitive, lowercase.
- Times: 24-hour «09:32»; relative days «сьогодні, 09:32», «вчора».
- Fractions of a total: «1,2 / 2 л», «88 / 110 г», «Використано 1 з 2», «Реєстрація · крок 2 з 3».

## Fixed names and terms

| Use | Never |
| --- | --- |
| FreeCook | Free Cook, Freecook |
| AI-кухар | ШІ-кухар, AI кухар, чат-бот |
| холодильник (also «Наш холодильник» as a default name) | склад, інвентар |
| Використайте першими | Скоро зіпсується (as a section title) |
| Покупки, список покупок | кошик |
| Щоденник рецептів | книга рецептів, збережене |
| Калорії, таблиця калорійності | трекер |
| Водний баланс | вода-трекер |
| списати | видалити (when quantity is used up) |
| Учасники і запрошення | друзі, команда |

## Examples from the design

- Hints: «Не прийшов лист? Надіслати ще раз через 0:58 · перевірте «Спам»».
- Empty dividers: «або без пароля», «або вручну».
- Toggle meta: «Нагадує, поки не досягнете норми · 2 л», «Вкладка «Калорії» · ціль: скинути».
- AI substitution: «Кисломолочного сиру немає — замінив грецьким йогуртом. Смак буде трохи інший, ніжніший.»
- Receipt: «Пакет і серветки пропущено — це не їжа».
- Recipes: «Усі продукти є вдома», «Бракує: буряк, рукола».
