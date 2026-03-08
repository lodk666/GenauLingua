"""
Українська локалізація для GenauLingua Bot
"""

TEXTS = {
    # ============================================================================
    # КНОПКИ ГОЛОВНОГО МЕНЮ
    # ============================================================================
    "btn_learn_words": "📚 Вчити слова",
    "btn_stats": "📊 Статистика",
    "btn_settings": "🦾 Налаштування",
    "btn_help": "❓ Допомога",
    "btn_back": "◀️ Назад",
    "menu_placeholder": "Обери дію...",

    # ============================================================================
    # ВІТАННЯ ТА СТАРТ
    # ============================================================================
    "welcome_title": "👋 <b>Привіт, {name}!</b>",
    "welcome_description": "🇩🇪 <b>GenauLingua</b> — вчи німецьку щодня.\nБот аналізує твої результати і підбирає слова саме для тебе.",
    "welcome_separator": "──────────────────",

    "welcome_learn_words_title": "📚 <b>Вчити слова</b>",
    "welcome_learn_words_desc": "Ігрові вікторини з німецьких слів. Чим більше займаєшся — тим точніше підбираються слова.",

    "welcome_stats_title": "📊 <b>Статистика</b>",
    "welcome_stats_desc": "Прогрес за рівнями, історія вікторин, порівняння з іншими користувачами.",

    "welcome_settings_title": "🦾 <b>Налаштування</b>",
    "welcome_settings_desc": "Рівень (A1–C2), мова інтерфейсу, режим вікторини.",

    "welcome_help_title": "❓ <b>Допомога</b>",
    "welcome_help_desc": "Підказки, актуальні оновлення та зворотній зв'язок.",

    "welcome_your_level": "Твій рівень: <b>{level}</b>\nРежим: <b>{mode}</b>",
    "welcome_call_to_action": "Натисни 📚 Вчити слова — і почнемо!",

    "welcome_choose_level": "Для початку обери свій рівень німецької:",
    "choose_level_prompt": "Обери рівень:",

    "level_selected": "✅ Рівень <b>{level}</b> обрано.\n\nНатисни 📚 Вчити слова — і почнемо!",
    "level_locked": "🔒 Цей рівень поки в розробці",

    # ============================================================================
    # НАГАДУВАННЯ
    # ============================================================================
    "notif_title": "🔔 <b>Налаштування нагадувань</b>",
    "notif_status": "Статус: {status}",
    "notif_status_on": "🔔 Увімкнені",
    "notif_status_off": "🔕 Вимкнені",
    "notif_time": "Час: {time}",
    "notif_days": "Дні: {days}",
    "notif_timezone": "Часовий пояс: {timezone}",
    "notif_hint": "💡 Нагадування приходитимуть у зазначений час за вашим часовим поясом.",
    "notif_hint_off": "💡 Увімкніть нагадування, щоб не забувати займатися щодня!",

    "notif_btn_toggle_on": "🔔 Нагадування: Увімкнено",
    "notif_btn_toggle_off": "🔕 Нагадування: Вимкнено",
    "notif_btn_time": "🕐 Час: {time}",
    "notif_btn_days": "📅 Обрати дні",
    "notif_btn_timezone": "🌍 Змінити часовий пояс",

    "notif_timezone_title": "🌍 <b>Оберіть ваш часовий пояс</b>",
    "notif_timezone_current": "Поточний: {timezone}",
    "notif_timezone_prompt": "Оберіть місто у вашому часовому поясі:",
    "notif_timezone_more": "🌍 Обрати інше місто ▼",
    "notif_timezone_back": "◀️ Назад",
    "notif_timezone_set": "✅ Часовий пояс встановлено: {city}",

    "notif_time_title": "🕐 <b>Оберіть час нагадування</b>",
    "notif_time_current": "Поточний час: {time}",
    "notif_time_timezone": "Часовий пояс: {timezone}",
    "notif_time_hint": "Нагадування приходитиме щодня у обраний час.",
    "notif_time_set": "✅ Час встановлено: {time}",

    "notif_days_title": "📅 <b>Оберіть дні для нагадувань</b>",
    "notif_days_hint": "Натисніть на день, щоб увімкнути/вимкнути його.\n✅ Зелена галочка - день увімкнено\n❌ Червоний хрестик - день вимкнено\n\nКоли закінчите - натисніть 'Зберегти'.",
    "notif_days_all": "📅 Всі дні",
    "notif_days_weekdays": "🗓️ Будні (Пн-Пт)",
    "notif_days_save": "💾 Зберегти",
    "notif_days_saved": "✅ Дні збережено!",
    "notif_days_all_selected": "✅ Обрано всі дні",
    "notif_days_weekdays_selected": "✅ Обрано будні (Пн-Пт)",
    "notif_days_none": "⚠️ Оберіть хоча б один день для нагадувань!",

    "notif_toggle_on": "🔔 Нагадування увімкнено!",
    "notif_toggle_off": "🔕 Нагадування вимкнено",

    "notif_message_title": "{emoji} <b>Час займатися!</b>",
    "notif_message_streak": "🔥 Стрік: {days} днів поспіль",
    "notif_message_words": "📊 Вивчено слів: {count}",
    "notif_message_cta": "💪 Не перериваю свою серію!",
    "notif_message_btn_start": "📚 Почати вікторину",
    "notif_message_btn_disable": "🔕 Вимкнути нагадування",

    "day_mon": "Пн",
    "day_tue": "Вт",
    "day_wed": "Ср",
    "day_thu": "Чт",
    "day_fri": "Пт",
    "day_sat": "Сб",
    "day_sun": "Нд",

    "notif_btn_back": "◀️ Назад до налаштувань",

    # Ключі для покращених сповіщень
    "notif_default_name": "друже",
    "notif_message_greeting": "🔥 <b>Час практики, {name}!</b>",
    "notif_message_progress_title": "📊 <b>Твій прогрес:</b>",
    "notif_progress_streak": "├ Серія: {days} днів 🎯",
    "notif_progress_quizzes": "├ Вікторин пройдено: {count}",
    "notif_progress_words": "├ Слів вивчено: {count}",
    "notif_progress_accuracy": "└ Точність: {percent}%",

    "notif_motivation_1": "Крок за кроком ти досягаєш результату!",
    "notif_motivation_2": "Твоя серія зростає — продовжуй у тому ж дусі!",
    "notif_motivation_3": "Сьогодні ще один крок до вільного володіння німецькою!",
    "notif_motivation_4": "Маленькі зусилля кожен день = великий результат!",
    "notif_motivation_5": "Ти на правильному шляху! Не зупиняйся!",
    "notif_motivation_6": "Кожна вікторина наближає тебе до мети!",

    # ============================================================================
    # НАЛАШТУВАННЯ
    # ============================================================================
    "settings_title": "🦾 <b>Налаштування</b>",
    "settings_level": "📚 Рівень: <b>{level}</b>",
    "settings_mode": "🔄 Режим: <b>{mode}</b>",
    "settings_language": "🌍 Мова інтерфейсу: <b>{language}</b>",
    "settings_choose": "Обери, що хочеш змінити:",

    "settings_btn_change_level": "📚 Змінити рівень",
    "settings_btn_change_mode": "🔄 Режим перекладу",
    "settings_btn_change_language": "🌍 Мова інтерфейсу",
    "settings_btn_notifications": "🔔 Нагадування",

    "settings_level_title": "📚 <b>Вибір рівня</b>",
    "settings_level_description": "Обери свій поточний рівень володіння німецькою мовою:\n\n• <b>A1</b> — Початковий (Привіт, як справи?)\n• <b>A2</b> — Базовий (Прості діалоги)\n• <b>B1</b> — Середній (Повсякденне спілкування)",

    "settings_mode_title": "🔄 <b>Режим перекладу</b>",
    "settings_mode_description": "Обери напрямок перекладу:",
    "settings_mode_hint_de_ru": "💡 DE→RU легше — можна вгадати за логікою",
    "settings_mode_hint_ru_de": "💡 RU→DE складніше — краще закріплює слова",
    "settings_mode_hint_de_uk": "💡 DE→UK легше — можна вгадати за логікою",
    "settings_mode_hint_uk_de": "💡 UK→DE складніше — краще закріплює слова",
    "settings_mode_hint_de_en": "💡 DE→EN easier — you can guess from context",
    "settings_mode_hint_en_de": "💡 EN→DE harder — better memorization",
    "settings_mode_hint_de_tr": "💡 DE→TR daha kolay — mantıkla tahmin edebilirsiniz",
    "settings_mode_hint_tr_de": "💡 TR→DE daha zor — kelimeleri daha iyi pekiştirir",

    "settings_language_title": "🌍 <b>Мова інтерфейсу</b>",
    "settings_language_description": "Обери мову інтерфейсу бота:",

    "language_changed": "✅ Мову змінено на {language}",
    "level_not_selected": "Не обрано",
    "user_not_found": "❌ Користувача не знайдено. Використай /start",

    # Назви мов
    "lang_ru": "🏴 Русский",
    "lang_uk": "🇺🇦 Українська",
    "lang_en": "🇬🇧 English",
    "lang_tr": "🇹🇷 Türkçe",

    # Режими перекладу
    "mode_de_to_ru": "🇩🇪 DE → 🏴 RU",
    "mode_ru_to_de": "🏴 RU → 🇩🇪 DE",
    "mode_de_to_uk": "🇩🇪 DE → 🇺🇦 UK",
    "mode_uk_to_de": "🇺🇦 UK → 🇩🇪 DE",

    # ============================================================================
    # ВІКТОРИНА
    # ============================================================================
    "quiz_no_level": "⚠️ Спочатку обери свій рівень за допомогою команди /start",
    "quiz_error_generation": "❌ Сталася помилка при підготовці вікторини.\nСпробуй ще раз через /start",
    "quiz_no_words": "❌ На жаль, для цього рівня поки немає слів.\nСпробуй обрати інший рівень.",

    "quiz_question_number": "Запитання {current}/{total}",
    "quiz_question_choose_word": "Обери правильне слово:",
    "quiz_question_choose_translation": "Обери правильний переклад:",

    "quiz_correct": "✅ <b>Правильно!</b>",
    "quiz_wrong": "❌ <b>Неправильно!</b>",
    "quiz_correct_answer": "Правильна відповідь:",

    "quiz_btn_next": "Далі →",
    "quiz_btn_repeat_errors": "🔄 Повторити помилки",

    "quiz_completed": "🎉 <b>Вікторину завершено!</b>",
    "quiz_result_correct": "✅ Правильно: <b>{correct}/{total}</b>",
    "quiz_result_percentage": "📈 Результат: <b>{percentage}%</b>",
    "quiz_result_details": "📝 <b>Деталі:</b>",
    "quiz_result_errors": "❌ Помилок: {count}",

    "quiz_repeat_title": "🔄 <b>Повтор помилок</b>",
    "quiz_repeat_question": "🔄 Повтор {current}/{total}",
    "quiz_no_errors": "✅ У тебе не було помилок!",
    "quiz_error_next": "❌ Не вдалося завантажити наступне запитання.",
    "quiz_error_generate": "❌ Не вдалося згенерувати наступне запитання.",

    # ============================================================================
    # СТАТИСТИКА
    # ============================================================================
    "stats_title": "📊 <b>Статистика</b>",
    "stats_no_level": "⚠️ <b>Спочатку обери рівень!</b>\n\nВикористай команду /start щоб почати.",

    "stats_all_words": "📚 Вся база ({count} слово|слова|слів)",
    "stats_learned": "✅ Вивчено: {count}",
    "stats_in_progress": "🔄 В процесі: {count}",
    "stats_new": "🆕 Нових: {count}",
    "stats_difficult": "❌ Складні: {count}",

    "stats_level_title": "🎯 Рівень {level} · {mode} ({count} слово|слова|слів)",
    "stats_quizzes_title": "🏆 <b>Вікторини (рівень {level}):</b>",
    "stats_quizzes_passed": "Пройдено: {count}",
    "stats_quizzes_avg": "Середній результат: {percentage}%",
    "stats_quizzes_best": "Найкращий результат: {percentage}%",
    "stats_quizzes_none": "Ти ще не проходив вікторини на цьому рівні.",

    "stats_activity_title": "🔥 <b>Активність:</b>",
    "stats_streak": "└─ Стрік: <b>{days}</b> днів поспіль",

    "stats_recent_title": "<b>Останні вікторини:</b>",
    "stats_learned_explanation": "💡 <b>Вивчено</b> — 3 правильні відповіді підряд по слову",

    # ============================================================================
    # ДОПОМОГА
    # ============================================================================
    "help_title": "❓ <b>Допомога — GenauLingua</b>",
    "help_description": "Тут ти знайдеш інструкції, дізнаєшся що скоро з'явиться в боті та як зв'язатися зі спільнотою.",
    "help_choose": "Обери розділ:",

    "help_btn_how_to_use": "📖 Як користуватися",
    "help_btn_roadmap": "🚀 Скоро в боті",
    "help_btn_community": "💬 Спільнота",
    "help_btn_about": "ℹ️ Про бота",

    # Як користуватися
    "help_how_to_use_title": "📖 <b>Як користуватися ботом</b>",
    "help_how_to_use_text": """1️⃣ <b>Налаштуй рівень і режим</b>
🦾 Налаштування → обери рівень A1–B1, режим перекладу та мову інтерфейсу.

2️⃣ <b>Вчи слова щодня</b>
📚 Вчити слова → вікторина з 25 слів.
Бот запам'ятовує твої помилки і частіше показує складні слова.

3️⃣ <b>Повторюй помилки</b>
Після вікторини можеш одразу повторити слова, в яких помилився.

4️⃣ <b>Стеж за прогресом</b>
📊 Статистика → скільки вивчено, історія вікторин, стрік.

5️⃣ <b>Змагайся з іншими</b>
🏆 Мій рейтинг → твої бали за місяць та за весь час.
📊 Таблиця лідерів → топ-10 серед усіх учасників.

6️⃣ <b>Налаштуй нагадування</b>
🦾 Налаштування → 🔔 Нагадування → обери час, дні та часовий пояс.
Бот нагадає тобі позайматися і покаже поточний стрік.

━━━━━━━━━━━━━━━━━
💡 Слово <b>вивчено</b> — якщо відповів правильно 3 рази поспіль.
🔥 <b>Стрік</b> зростає якщо пройшов хоча б 1 вікторину в цей день.

Питання? → t.me/genaulingua_chat""",

    # Скоро в боті
    "help_roadmap_title": "🚀 <b>Скоро в GenauLingua</b>",
    "help_roadmap_text": """🏆 <b>Досягнення</b>
Беджі за прогрес — перша вікторина, 7 днів поспіль, 100 слів вивчено, вікторина на 100% та інші.

🗂️ <b>Категорії слів</b>
Вчи слова за темами — їжа, транспорт, робота, подорожі та інші.

📚 <b>Рівні B2–C2</b>
Зараз доступні A1–B1. В роботі база для B2, C1 і C2.

📖 <b>30 000 слів</b>
Розширення бази до 30 000 слів з перекладами на всі 4 мови.

🔄 <b>Нові режими навчання</b>
Більше форматів для вивчення слів — не тільки вікторини.

━━━━━━━━━━━━━━━━━
💬 Ідеї та побажання — пиши в чат:
t.me/genaulingua_chat""",

    # Спільнота
    "help_community_title": "💬 <b>Спільнота GenauLingua</b>",
    "help_community_text": """👉 <b>t.me/genaulingua_chat</b>

У чаті:
📢 Першими дізнаєшся про оновлення
🐛 Знайшов баг — пиши або присилай скріншот
📝 Помилка в перекладі — повідомляй, виправимо
💡 Ідеї та побажання — все читаємо і беремо в роботу
👥 Спілкування з іншими учнями

━━━━━━━━━━━━━━━━━
Чим активніша спільнота — тим кращим стає бот. Не соромся! 🙌""",

    # Про бота
    "help_about_title": "ℹ️ <b>Про бота</b>",
    "help_about_text": """🤖 <b>GenauLingua</b> — персональний помічник у вивченні німецької.

✨ <b>Що вміє:</b>
• База слів A1–B1 (3000+ слів)
• Розумний підбір слів — SRS алгоритм
• 4 мови: DE↔RU, DE↔UA, DE↔EN, DE↔TR
• Повтор помилок після вікторини
• Статистика, стрік та прогрес-бар
• Місячний рейтинг та таблиця лідерів
• Нагадування з гнучким розкладом
• Інтерфейс російською, українською, англійською та турецькою

📅 <b>Оновлено:</b> Березень 2026

💬 Стеж за оновленнями: t.me/genaulingua_chat""",

    # ============================================================================
    # РЕЙТИНГ — МІЙ РЕЙТИНГ
    # ============================================================================
    "rating_title_monthly": "🏆 <b>Мій рейтинг — {month} {year}</b>",
    "rating_not_active": "❌ Рейтинг поки не активний.",
    "rating_not_in_ranking": "📍 Ти ще не в рейтингу",
    "rating_start_quiz": "🚀 Пройди першу вікторину!",
    "rating_position": "📍 Позиція: <b>#{rank}</b> з {total}",
    "rating_points": "💎 Бали: <b>{score}</b>",
    "rating_your_month": "⭐ <b>Твій {month}:</b>",
    "rating_quizzes": "├ Вікторин: {count}",
    "rating_words_learned": "├ Вивчено слів: {count}",
    "rating_streak": "├ Стрік: {count} дн.",
    "rating_avg_result": "└ Середній результат: {percent}%",
    "rating_goal": "🎯 До #{rank} ({name}): ще {diff} балів",
    "rating_scoring_title": "💡 <b>Як заробити бали:</b>",
    "rating_scoring_quiz": "• Пройдена вікторина → +10",
    "rating_scoring_reverse": "• Режим «Реверс» → +5",
    "rating_scoring_word": "• Вивчене слово → +2",
    "rating_scoring_streak": "• День поспіль → +3",
    "rating_scoring_bonus": "• Точність 90%+ → +50 бонус",

    "rating_title_alltime": "🏆 <b>Мій рейтинг — За весь час</b>",
    "rating_position_alltime": "📍 Позиція: <b>#{rank}</b>",
    "rating_position_none": "📍 Позиція: <b>—</b>",
    "rating_achievements": "⭐ <b>Твої досягнення:</b>",
    "rating_wins": "├ Перемог (1 місце): {count}",
    "rating_total_words": "└ Вивчено слів: {count}",
    "rating_motivation_start": "🚀 Почни вчити слова — перший крок найважливіший!",
    "rating_motivation_continue": "🎯 Продовжуй — перша перемога вже близько!",
    "rating_motivation_champion": "🔥 Ти справжній чемпіон!",
    "rating_lifetime_title": "🌟 <b>Lifetime бали — це:</b>",
    "rating_lifetime_desc": "• Всі бали за всі місяці\n• +100 за 🥇 · +50 за 🥈 · +25 за 🥉",

    "table_title_monthly": "📊 <b>Таблиця лідерів — {month} {year}</b>",
    "table_title_alltime": "📊 <b>Таблиця лідерів — За весь час</b>",
    "table_empty": "Поки ніхто не бере участь.\nПройди вікторину першим! 💪",
    "table_you_in_top": "📍 Ти: <b>#{rank}</b> з {total}",
    "table_you_not_in_top": "📍 Ти: <b>#{rank}</b> з {total} — {score} балів",
    "table_you_outside": "📍 Ти: за межами топ-10 — {score} балів",
    "table_you_not_ranked": "📍 Ти ще не в рейтингу",
    "table_points": "балів",
    "btn_leaderboard_table": "📊 Таблиця лідерів",
    "btn_back_to_rating": "◀️ Назад до рейтингу",

    # СТАТИСТИКА
    "stats_header": "📊 <b>Твоя статистика</b>",
    "stats_learned_of": "└─ Вивчено <b>{learned}</b> з {total}",
    "stats_details": "🔄 В процесі: {progress}\n🆕 Нових: {new}\n⚠️ Складних: {difficult}",
    "stats_achievements_title": "<b>Твої досягнення</b>",
    "stats_words_count": "├─ Вивчено слів: <b>{count}</b>",
    "stats_streak_line": "└─ Стрік: <b>{days} днів поспіль</b>",
    "stats_quizzes_header": "<b>Вікторини ({level})</b>",
    "stats_quizzes_passed_line": "├─ Пройдено: <b>{count}</b>",
    "stats_quizzes_avg_line": "├─ Середній результат: <b>{percent}%</b>",
    "stats_quizzes_best_line": "└─ Найкращий результат: <b>{percent}%</b>",
    "stats_quizzes_empty": "└─ Поки немає пройдених вікторин",
    "stats_recent_header": "📈 <b>Останні вікторини</b>",
    "stats_overall_header": "🌍 <b>Загальний прогрес</b>",
    "stats_overall_learned": "└─ Вивчено <b>{learned}</b> з {total} слів",
    "stats_cta_start": "💪 Почни вчити слова — перший крок найважливіший!",
    "stats_cta_begin": "🚀 Чудовий початок! Продовжуй так само!",
    "stats_cta_halfway": "🔥 Ти на півдорозі! Не зупиняйся!",
    "stats_cta_almost": "🏆 Майже біля мети! Молодець!",
    "stats_explanation": "—————————————————————\nСлово вивчено = 3 правильних відповіді поспіль",
    "stats_btn_rating": "🏆 Мій рейтинг",
}