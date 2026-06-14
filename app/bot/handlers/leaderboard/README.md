# 🏆 Система месячного и lifetime рейтинга

Полная документация модуля рейтингов для GenauLingua бота.

---

## 📁 Структура файлов

```
app/bot/handlers/leaderboard/
├── __init__.py              # Регистрация роутеров
├── monthly.py               # Месячный рейтинг
├── alltime.py               # Lifetime рейтинг
├── leaderboard_table.py     # Таблица лидеров
└── utils.py                 # Утилиты и форматирование

app/services/
└── monthly_leaderboard_service.py  # Бизнес-логика и БД
```

---

## 💰 Формула начисления баллов

### Месячные баллы:
```python
monthly_score = (
    monthly_quizzes * 10      # Викторина
    + monthly_reverse * 5     # Реверс
    + monthly_words * 2       # Выученные слова
    + monthly_streak * 3      # Дни подряд
    + accuracy_bonus          # 90%+ → +50, 80%+ → +30, 70%+ → +15
    + report_bonus            # Подтверждённые репорты → +1 каждый
)
```

### Lifetime баллы:
```python
lifetime_score = sum(monthly_scores) + award_bonuses
# 🥇 1 место → +100
# 🥈 2 место → +50
# 🥉 3 место → +25
# 4-10 место → +10
```

---

## 🗄️ Таблицы БД

| Таблица | Назначение |
|---------|-----------|
| `monthly_seasons` | Месячные сезоны соревнований |
| `monthly_stats` | Статистика пользователя за месяц |
| `monthly_quiz_events` | Идемпотентность (викторина учитывается 1 раз) |
| `monthly_awards` | Награды за места в топ-10 |
| `win_streaks` | Серии месячных побед |

---

## 🔄 Жизненный цикл сезона

1. **Начало месяца (1 число):** `create_new_season()` — новый сезон, предыдущий деактивируется
2. **В течение месяца:** после каждой викторины — `update_monthly_stats()` (инкрементально)
3. **Конец месяца:** `finalize_season()` — награды топ-10, обновление lifetime_score

---

## 🎨 Логика отображения

- **Топ-3:** только медали 🥇🥈🥉, без титулов
- **4-10 места:** номер + титул (win streak: 🔥, 👑, 💎 / по словам: 📚, 🎯, 🧠, 🌍)
- **Текущий пользователь:** жирный шрифт на любой позиции

---

## 🌍 Локализация

4 языка: RU, UK, EN, TR — названия месяцев, тексты кнопок, пояснения, формулы баллов.

---

## ⚙️ Критические моменты

1. **Порядок регистрации роутеров** — leaderboard ПЕРВЫМ в `main.py` (перехват `show_my_rating`)
2. **Идемпотентность** — через `UNIQUE(quiz_session_id)` в `monthly_quiz_events`
3. **`User.display_name`** — имя + фамилия, без @

---

## 📊 Использование

```python
# После завершения викторины:
from app.services.monthly_leaderboard_service import update_monthly_stats
await update_monthly_stats(user_id=user.id, session=session, quiz_session_id=session_id)

# Получить рейтинг:
from app.services.monthly_leaderboard_service import get_monthly_leaderboard
leaderboard = await get_monthly_leaderboard(session, season_id=season.id, limit=10)

# Подвести итоги:
from app.services.monthly_leaderboard_service import finalize_season
await finalize_season(season_id=season.id, session=session)
```