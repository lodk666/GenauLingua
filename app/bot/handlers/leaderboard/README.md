# 🏆 Система месячного и lifetime рейтинга

Полная документация модуля рейтингов для GenauLingua бота.

---

## 📁 Структура файлов

```
app/bot/handlers/leaderboard/
├── __init__.py              # Регистрация роутеров
├── monthly.py               # Месячный рейтинг
├── alltime.py               # Lifetime рейтинг
├── personal.py              # Личная карточка (TODO)
└── utils.py                 # Утилиты и форматирование

app/services/
└── monthly_leaderboard_service.py  # Бизнес-логика и БД
```

---

## 🎯 Назначение файлов

### **1. `__init__.py`**
Регистрирует все роутеры модуля для использования в `main.py`.

**Экспортирует:**
- `monthly_router` — обработчики месячного рейтинга
- `alltime_router` — обработчики lifetime рейтинга
- `personal_router` — личная карточка месяца (заглушка)

---

### **2. `monthly.py`** — Месячный рейтинг

**Обработчики:**
- `/leaderboard` — показать месячный рейтинг
- `show_my_rating` (callback) — открыть рейтинг из статистики
- `leaderboard_monthly` (callback) — переключение на вкладку "Месяц"

**Что показывает:**
- 🏆 Топ-10 игроков текущего месяца
- 📍 Позицию пользователя (#X из Y)
- 💎 Баллы пользователя
- 🎯 Прогресс до топ-3 (если не в топ-3)
- 💡 Формулу начисления баллов

**Ключевые функции:**
```python
format_monthly_leaderboard()  # Форматирует текст рейтинга
get_leaderboard_keyboard()    # Клавиатура с вкладками
```

**Зависимости:**
- `app.services.monthly_leaderboard_service` — получение данных
- `app.bot.handlers.leaderboard.utils` — форматирование
- `app.database.models.User` — модель пользователя

---

### **3. `alltime.py`** — Lifetime рейтинг

**Обработчики:**
- `leaderboard_alltime` (callback) — переключение на вкладку "За всё время"

**Что показывает:**
- 🏆 Топ-10 игроков за всё время
- 📍 Позицию пользователя
- 💎 Lifetime баллы
- 🏆 Побед в топ-3
- 📚 Слов выучено
- 💡 Объяснение что такое Lifetime баллы

**Ключевые функции:**
```python
format_alltime_card()         # Форматирует карточку пользователя
get_leaderboard_keyboard()    # Клавиатура с вкладками
```

**Зависимости:**
- `app.services.monthly_leaderboard_service.get_lifetime_leaderboard` — данные
- `app.bot.handlers.leaderboard.utils` — форматирование

---

### **4. `personal.py`** — Личная карточка месяца

**Статус:** Заглушка (TODO)

**Планируется:**
- Детальная статистика за текущий месяц
- Прогресс (было/стало)
- Достижения месяца
- Сравнение с прошлым месяцем

---

### **5. `utils.py`** — Утилиты и форматирование

**Функции:**

#### Титулы и эмодзи:
```python
get_win_streak_emoji(current_streak: int) -> str
# Возвращает эмодзи для серии побед:
# 1 → 🔥, 2 → 🔥×2, 3-4 → 👑×N, 5+ → 💎×N

get_words_emoji(learned_words: int) -> str
# Возвращает эмодзи по количеству слов:
# 100+ → 📚, 500+ → 🎯, 1000+ → 🧠, 2000+ → 🌍

get_user_title(win_streak: dict, learned_words: int) -> str
# Приоритет: win streak > титул по словам
```

#### Форматирование:
```python
format_month_name(month: int, lang: str) -> str
# Название месяца на 4 языках (ru, uk, en, tr)

create_progress_bar(current: int, target: int, length: int) -> str
# Визуальный прогресс-бар: ▓▓▓▓▓░░░░░ 50%

format_user_card(entry: dict, rank: int, is_current_user: bool, lang: str) -> str
# Форматирует карточку пользователя:
# - Топ-3: только медали 🥇🥈🥉
# - Остальные: медали + титулы
# - Текущий: жирный шрифт <b>имя</b>
```

#### Локализация:
```python
get_leaderboard_keyboard_text(lang: str, current_tab: str) -> dict
# Тексты кнопок переключения вкладок

get_localized_text(key: str, lang: str) -> str
# Локализованные тексты для рейтинга
```

---

### **6. `monthly_leaderboard_service.py`** — Бизнес-логика

**Основные функции:**

#### Управление сезонами:
```python
get_current_season(session) -> MonthlySeason
# Получить текущий активный сезон

create_new_season(year: int, month: int, session) -> MonthlySeason
# Создать новый месячный сезон (вызывается 1 числа)

get_or_create_current_season(session) -> MonthlySeason
# Получить текущий или создать если нет
```

#### Обновление статистики:
```python
update_monthly_stats(user_id, session, quiz_session_id) -> MonthlyStats
# Обновить статистику пользователя после викторины
# - Идемпотентно (защита от дублей через MonthlyQuizEvent)
# - O(1) инкрементальное обновление
# - Автоматически пересчитывает баллы
```

#### Получение рейтингов:
```python
get_monthly_leaderboard(session, season_id, limit=50) -> List[Dict]
# Возвращает топ-N пользователей текущего месяца
# Поля: rank, user_id, display_name, monthly_score, win_streak, awards

get_user_monthly_rank(user_id, session, season_id) -> Dict
# Позиция пользователя в месячном рейтинге
# Поля: rank, total_users, monthly_score, percentile

get_lifetime_leaderboard(session, limit=50) -> List[Dict]
# Возвращает топ-N по lifetime баллам
# Поля: rank, user_id, display_name, lifetime_score, total_wins, words_learned
```

#### Подведение итогов:
```python
finalize_season(season_id, session)
# Подведение итогов месяца (вызывается в последний день):
# - Проставляет финальные ранги
# - Выдаёт награды топ-10
# - Обновляет lifetime_score
# - Обновляет серии побед

update_win_streak(user_id, season_id, session)
# Обновляет серию месячных побед
```

---

## 🗄️ База данных

### **Таблицы:**

#### `monthly_seasons`
```sql
id, year, month, start_date, end_date, 
is_active, winners_finalized, created_at
```
**Назначение:** Хранит месячные сезоны

#### `monthly_stats`
```sql
id, user_id, season_id, monthly_score,
monthly_quizzes, monthly_reverse, monthly_words,
monthly_streak, monthly_avg_percent,
total_correct, total_questions, final_rank,
last_quiz_date, created_at, updated_at
```
**Назначение:** Статистика пользователя за месяц

#### `monthly_quiz_events`
```sql
id, quiz_session_id, user_id, season_id, created_at
UNIQUE(quiz_session_id)
```
**Назначение:** Гарантирует идемпотентность (викторина учитывается 1 раз)

#### `monthly_awards`
```sql
id, user_id, season_id, rank, 
award_type (gold/silver/bronze/top10),
lifetime_bonus, created_at
```
**Назначение:** Награды за места в топ-10

#### `win_streaks`
```sql
id, user_id, current_streak, best_streak,
total_wins, last_win_season, created_at, updated_at
```
**Назначение:** Серии месячных побед (1 место подряд)

---

## 💰 Формула начисления баллов

### **Месячные баллы:**
```python
monthly_score = (
    monthly_quizzes * 10      # Викторина
    + monthly_reverse * 5     # Реверс
    + monthly_words * 2       # Выученные слова
    + monthly_streak * 3      # Дни подряд
    + (50 if avg >= 90 else 0)  # Бонус за 90%+
    + (30 if avg >= 80 else 0)  # Бонус за 80%+
)
```

### **Lifetime баллы:**
```python
lifetime_score = sum(monthly_scores) + award_bonuses
# award_bonuses:
#   🥇 1 место → +100
#   🥈 2 место → +50
#   🥉 3 место → +25
#   4-10 место → +10
```

---

## 🔄 Логика работы

### **Жизненный цикл сезона:**

1. **Начало месяца (1 число):**
   - `create_new_season()` создаёт новый сезон
   - Предыдущий сезон деактивируется

2. **В течение месяца:**
   - После каждой викторины вызывается `update_monthly_stats()`
   - Инкрементально обновляются баллы

3. **Конец месяца (последний день):**
   - `finalize_season()` подводит итоги
   - Выдаются награды топ-10
   - Обновляются lifetime_score

### **Обновление статистики (после викторины):**

```python
# В app/bot/handlers/quiz/game.py после завершения викторины:

from app.services.monthly_leaderboard_service import update_monthly_stats

# Обновляем месячную статистику
await update_monthly_stats(
    user_id=user.id,
    session=session,
    quiz_session_id=quiz_session.id
)
```

**Что происходит:**
1. Проверка дубликата (через `monthly_quiz_events`)
2. Инкрементальное обновление счётчиков
3. Пересчёт среднего процента
4. Подсчёт выученных слов за месяц
5. Вычисление стрика дней
6. Расчёт итоговых баллов

---

## 🎨 Дизайн и UI

### **Логика отображения:**

#### **Топ-3:**
- Только медали: 🥇 🥈 🥉
- **БЕЗ** титулов
- Формат:
  ```
  🥇 Имя Фамилия
     💎 1500 баллов
  ```

#### **4-10 места:**
- Номер + титул (если есть)
- Титулы:
  - Win streak: 🔥 🔥×2 👑×3 💎×5
  - По словам: 📚 🎯 🧠 🌍
- Формат:
  ```
  4. Имя 🔥×3 — 1200 баллов
  ```

#### **Текущий пользователь:**
- **Жирный шрифт** `<b>имя</b>`
- На любой позиции

### **Компоненты интерфейса:**

```
🏆 Рейтинг Март 2026          ← Заголовок

🥇 Игрок 1                     ← Топ-3 (медали)
   💎 2000 баллов

4. Игрок 4 🔥×2 — 1500 баллов  ← 4-10 (титулы)

━━━━━━━━━━━━━━━━━              ← Разделитель

📍 Твоя позиция: #5            ← Блок пользователя
💎 Баллы: 1200
📊 5 из 100

🎯 До топ-3:                   ← Прогресс (если не в топ-3)
▓▓▓▓▓░░░░░ 60% (300 баллов)

━━━━━━━━━━━━━━━━━              ← Разделитель

💡 Как заработать баллы:       ← Формула
• Викторина → 10 баллов
• Реверс → +5 бонус
...
```

---

## 🌍 Локализация

Поддержка 4 языков:
- 🇷🇺 Русский (ru)
- 🇺🇦 Украинский (uk)
- 🇬🇧 Английский (en)
- 🇹🇷 Турецкий (tr)

**Локализованные элементы:**
- Названия месяцев
- Тексты кнопок
- Пояснения
- Формулы баллов

---

## 🔗 Связи с другими модулями

### **Импортируется в:**
```python
# app/main.py
from app.bot.handlers.leaderboard.monthly import router as monthly_router
from app.bot.handlers.leaderboard.alltime import router as alltime_router
from app.bot.handlers.leaderboard.personal import router as personal_router

dp.include_router(monthly_router)  # РАНЬШЕ quiz_router!
dp.include_router(alltime_router)
dp.include_router(personal_router)
```

### **Использует:**
```python
# Модели
from app.database.models import (
    User, MonthlySeason, MonthlyStats, 
    MonthlyQuizEvent, MonthlyAward, WinStreak
)

# Сервисы
from app.services.monthly_leaderboard_service import (
    get_monthly_leaderboard,
    get_user_monthly_rank,
    get_lifetime_leaderboard,
    get_current_season,
    update_monthly_stats
)

# Клавиатуры
from app.bot.keyboards import get_main_menu_keyboard
```

### **Вызывается из:**
```python
# app/bot/handlers/quiz/stats.py
# Кнопка "🏆 Мой рейтинг" → callback "show_my_rating"

# app/bot/handlers/quiz/game.py
# После завершения викторины → update_monthly_stats()
```

---

## ⚙️ Критические моменты

### **1. Порядок регистрации роутеров**
```python
# В main.py ОБЯЗАТЕЛЬНО:
dp.include_router(monthly_router)  # ПЕРВЫМ!
dp.include_router(alltime_router)
dp.include_router(personal_router)
dp.include_router(quiz_router)     # ПОСЛЕ leaderboard!
```
**Почему:** Callback `show_my_rating` должен обрабатываться `monthly.py`, а не `quiz/stats.py`

### **2. Идемпотентность**
Викторина учитывается **только 1 раз** через таблицу `monthly_quiz_events` с `UNIQUE(quiz_session_id)`

### **3. User.display_name**
```python
# app/database/models.py
@property
def display_name(self) -> str:
    if self.first_name:
        name = self.first_name
        if self.last_name:
            name += f" {self.last_name}"
        return name
    elif self.username:
        return self.username  # БЕЗ @!
    else:
        return f"User {self.id}"
```

### **4. Обновление lifetime_score**
Автоматически обновляется в `finalize_season()` в конце месяца + бонусы за топ-3.

---

## 🐛 Известные проблемы и решения

### **Проблема:** "Топ 0%"
**Решение:** Заменено на "X из Y" (например, "1 из 100")

### **Проблема:** "@username вместо имени"
**Решение:** Исправлено свойство `User.display_name`

### **Проблема:** "Средний ≥90% непонятно"
**Решение:** Заменено на "90%+ правильных"

### **Проблема:** `return leaderboard` отсутствует
**Решение:** Добавлена строка в конец `get_lifetime_leaderboard()`

---

## 📊 Примеры использования

### **Показать месячный рейтинг:**
```python
from app.services.monthly_leaderboard_service import (
    get_monthly_leaderboard,
    get_current_season
)

season = await get_current_season(session)
leaderboard = await get_monthly_leaderboard(
    session, 
    season_id=season.id, 
    limit=10
)

for entry in leaderboard:
    print(f"{entry['rank']}. {entry['display_name']} - {entry['monthly_score']}")
```

### **Обновить статистику после викторины:**
```python
from app.services.monthly_leaderboard_service import update_monthly_stats

await update_monthly_stats(
    user_id=user.id,
    session=session,
    quiz_session_id=quiz_session.id
)
```

### **Подвести итоги месяца:**
```python
from app.services.monthly_leaderboard_service import finalize_season

# Вызывается в последний день месяца
await finalize_season(season_id=season.id, session=session)
```

---

## 🚀 Развитие и TODO

### **Планируется:**
- [ ] Личная карточка месяца (`personal.py`)
- [ ] Уведомления о позиции в рейтинге
- [ ] Экспорт рейтинга в PDF/изображение
- [ ] Историческая статистика (прошлые месяцы)
- [ ] Достижения и бейджи
- [ ] Групповой рейтинг

---

## 📝 Changelog

### v1.0 (Март 2026)
- ✅ Месячный рейтинг
- ✅ Lifetime рейтинг
- ✅ Система баллов и наград
- ✅ Серии побед
- ✅ Локализация (4 языка)
- ✅ Прогресс-бары
- ✅ Титулы и эмодзи

---

**Автор:** Claude (Anthropic)  
**Дата:** Март 2026  
**Версия:** 1.0