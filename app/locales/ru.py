"""
Русская локализация для GenauLingua Bot
"""

TEXTS = {
    # ============================================================================
    # КНОПКИ ГЛАВНОГО МЕНЮ
    # ============================================================================
    "btn_learn_words": "📚 Учить слова",
    "btn_stats": "📊 Статистика",
    "btn_settings": "🦾 Настройки",
    "btn_help": "❓ Помощь",
    "btn_back": "◀️ Назад",
    "menu_placeholder": "Выбери действие...",

    # ============================================================================
    # ПРИВЕТСТВИЕ И СТАРТ
    # ============================================================================
    "welcome_title": "👋 <b>Привет, {name}!</b>",
    "welcome_description": "🇩🇪 <b>GenauLingua</b> — учи немецкий через игру\n12 000+ слов · 20 тем · 6 уровней\n\nБот подбирает слова под тебя — чем больше\nиграешь, тем умнее подбор",
    "welcome_separator": "──────────────────",

    "welcome_learn_words_title": "📚 <b>Учить слова</b>",
    "welcome_learn_words_desc": "Запуск викторины",

    "welcome_stats_title": "📊 <b>Статистика</b>",
    "welcome_stats_desc": "Твой прогресс",

    "welcome_settings_title": "🦾 <b>Настройки</b>",
    "welcome_settings_desc": "Режим, язык, темы",

    "welcome_help_title": "❓ <b>Помощь</b>",
    "welcome_help_desc": "Подсказки и обратная связь",

    "welcome_your_level": "Твой уровень: <b>{level}</b>\nРежим: <b>{mode}</b>",
    "welcome_call_to_action": "Нажми 📚 Учить слова — и начнём!",

    "welcome_choose_level": "🎯 <b>С чего начнём?</b>\n\nВыбери свой уровень немецкого\n\n• A1–A2 — базовая лексика\n• B1–B2 — уверенное общение\n• C1–C2 — свободное владение",
    "choose_level_prompt": "Выбери уровень:",

    "level_selected": "✅ Уровень <b>{level}</b> выбран.\n\nНажми 📚 Учить слова — и начнём!",
    "level_locked": "🔒 Этот уровень пока в разработке",

    # ============================================================================
    # НАПОМИНАНИЯ
    # ============================================================================
    "notif_title": "🔔 <b>Настройки напоминаний</b>",
    "notif_status": "Статус: {status}",
    "notif_status_on": "🔔 Включены",
    "notif_status_off": "🔕 Выключены",
    "notif_time": "Время: {time}",
    "notif_days": "Дни: {days}",
    "notif_timezone": "Часовой пояс: {timezone}",
    "notif_hint": "💡 Напоминания будут приходить в указанное время по вашему часовому поясу.",
    "notif_hint_off": "💡 Включите напоминания, чтобы не забывать заниматься каждый день!",

    "notif_btn_toggle_on": "🔔 Напоминания: Включено",
    "notif_btn_toggle_off": "🔕 Напоминания: Выключено",
    "notif_btn_time": "🕐 Время: {time}",
    "notif_btn_days": "📅 Выбрать дни",
    "notif_btn_timezone": "🌍 Изменить часовой пояс",

    "notif_timezone_title": "🌍 <b>Выберите ваш часовой пояс</b>",
    "notif_timezone_current": "Текущий: {timezone}",
    "notif_timezone_prompt": "Выберите город в вашем часовом поясе:",
    "notif_timezone_more": "🌍 Выбрать другой город ▼",
    "notif_timezone_back": "◀️ Назад",
    "notif_timezone_set": "✅ Часовой пояс установлен: {city}",

    "notif_time_title": "🕐 <b>Выберите время напоминания</b>",
    "notif_time_current": "Текущее время: {time}",
    "notif_time_timezone": "Часовой пояс: {timezone}",
    "notif_time_hint": "Напоминание будет приходить каждый день в выбранное время.",
    "notif_time_set": "✅ Время установлено: {time}",

    "notif_days_title": "📅 <b>Выберите дни для напоминаний</b>",
    "notif_days_hint": "Нажмите на день, чтобы включить/выключить его.\n✅ Зелёная галочка - день включен\n❌ Красный крестик - день выключен\n\nКогда закончите - нажмите 'Сохранить'.",
    "notif_days_all": "📅 Все дни",
    "notif_days_weekdays": "🗓️ Будни (Пн-Пт)",
    "notif_days_save": "💾 Сохранить",
    "notif_days_saved": "✅ Дни сохранены!",
    "notif_days_all_selected": "✅ Выбраны все дни",
    "notif_days_weekdays_selected": "✅ Выбраны будни (Пн-Пт)",
    "notif_days_none": "⚠️ Выберите хотя бы один день для напоминаний!",

    "notif_toggle_on": "🔔 Напоминания включены!",
    "notif_toggle_off": "🔕 Напоминания выключены",

    "notif_message_title": "{emoji} <b>Время заниматься!</b>",
    "notif_message_streak": "🔥 Стрик: {days} дней подряд",
    "notif_message_words": "📊 Выучено слов: {count}",
    "notif_message_cta": "💪 Не прерывай свою серию!",
    "notif_message_btn_start": "📚 Начать викторину",
    "notif_message_btn_disable": "🔕 Отключить напоминания",

    "day_mon": "Пн",
    "day_tue": "Вт",
    "day_wed": "Ср",
    "day_thu": "Чт",
    "day_fri": "Пт",
    "day_sat": "Сб",
    "day_sun": "Вс",

    "notif_btn_back": "◀️ Назад в настройки",

    "notif_default_name": "друг",
    "notif_message_greeting": "🔥 <b>Время практики, {name}!</b>",
    "notif_message_progress_title": "📊 <b>Твой прогресс:</b>",
    "notif_progress_streak": "├ Серия: {days} дней 🎯",
    "notif_progress_quizzes": "├ Викторин пройдено: {count}",
    "notif_progress_words": "├ Слов изучено: {count}",
    "notif_progress_accuracy": "└ Точность: {percent}%",

    "notif_motivation_1": "Шаг за шагом ты достигаешь результата!",
    "notif_motivation_2": "Твоя серия растёт — продолжай в том же духе!",
    "notif_motivation_3": "Сегодня ещё один шаг к свободному владению немецким!",
    "notif_motivation_4": "Маленькие усилия каждый день = большой результат!",
    "notif_motivation_5": "Ты на правильном пути! Не останавливайся!",
    "notif_motivation_6": "Каждна викторина приближает тебя к цели!",

    # ============================================================================
    # НАСТРОЙКИ
    # ============================================================================
    "settings_title": "🦾 <b>Настройки</b>",
    "settings_level": "📚 Уровень: <b>{level}</b>",
    "settings_mode": "🔄 Перевод: <b>{mode}</b>",
    "settings_language": "🌍 Язык интерфейса: <b>{language}</b>",
    "settings_choose": "Выбери, что хочешь изменить:",

    "settings_btn_quiz_mode": "📝 Режим викторины",
    "settings_btn_change_mode": "🔄 Режим перевода",
    "settings_btn_change_language": "🌍 Язык интерфейса",
    "settings_btn_notifications": "🔔 Напоминания",

    "settings_quiz_mode_line": "📝 Режим: <b>{mode}</b>",

    "settings_mode_title": "🔄 <b>Режим перевода</b>",
    "settings_mode_description": "Выбери направление перевода:",
    "settings_mode_hint_de_ru": "💡 DE→RU легче — можно угадать по логике",
    "settings_mode_hint_ru_de": "💡 RU→DE сложнее — лучше закрепляет слова",
    "settings_mode_hint_de_uk": "💡 DE→UK легше — можна вгадати за логікою",
    "settings_mode_hint_uk_de": "💡 UK→DE складніше — краще закріплює слова",
    "settings_mode_hint_de_en": "💡 DE→EN easier — you can guess from context",
    "settings_mode_hint_en_de": "💡 EN→DE harder — better memorization",
    "settings_mode_hint_de_tr": "💡 DE→TR daha kolay — mantıkla tahmin edebilirsiniz",
    "settings_mode_hint_tr_de": "💡 TR→DE daha zor — kelimeleri daha iyi pekiştirir",

    "settings_language_title": "🌍 <b>Язык интерфейса</b>",
    "settings_language_description": "Выбери язык интерфейса бота:",

    "language_changed": "✅ Язык изменён на {language}",
    "level_not_selected": "Не выбран",
    "user_not_found": "❌ Пользователь не найден. Используй /start",

    # Названия языков
    "lang_ru": "🏴 Русский",
    "lang_uk": "🇺🇦 Українська",
    "lang_en": "🇬🇧 English",
    "lang_tr": "🇹🇷 Türkçe",

    # Режимы перевода
    "mode_de_to_ru": "🇩🇪 DE → 🏴 RU",
    "mode_ru_to_de": "🏴 RU → 🇩🇪 DE",
    "mode_de_to_uk": "🇩🇪 DE → 🇺🇦 UK",
    "mode_uk_to_de": "🇺🇦 UK → 🇩🇪 DE",
    "mode_de_to_en": "🇩🇪 DE → 🇬🇧 EN",
    "mode_en_to_de": "🇬🇧 EN → 🇩🇪 DE",
    "mode_de_to_tr": "🇩🇪 DE → 🇹🇷 TR",
    "mode_tr_to_de": "🇹🇷 TR → 🇩🇪 DE",

    # ============================================================================
    # РЕЖИМ ВИКТОРИНЫ (НОВОЕ)
    # ============================================================================
    "qmode_title": "📝 <b>Режим викторины</b>",
    "qmode_current": "Сейчас: <b>{mode}</b>",
    "qmode_choose": "Выбери как хочешь учить слова\nМожешь изменить в любой момент — прогресс сохраняется",

    "qmode_btn_level": "📚 По уровню",
    "qmode_btn_category": "🗂 Категория",
    "qmode_btn_all": "🌍 Топ 10 тысяч",
    "qmode_btn_difficult": "⚠️ Сложные",

    "qmode_level_short": "📚 Уровень {level}",
    "qmode_category_short": "🗂 {category}",
    "qmode_all_short": "🌍 Топ 10 тысяч",
    "qmode_difficult_short": "⚠️ Сложные слова",

    "qmode_level_title": "📚 <b>Выбор уровня</b>",
    "qmode_level_desc": "От первого «Hallo» до свободных дискуссий\nВсе уровни доступны — выбирай свой!\n\n• A1–A2 — базовая лексика\n• B1–B2 — уверенное общение\n• C1–C2 — свободное владение",
    "qmode_level_set": "✅ Режим: По уровню ({level})",

    "qmode_category_title": "🗂 <b>Выбор категории</b>",
    "qmode_category_desc": "От еды до науки — выбери тему, которая тебе нужна\n\nКаждая категория содержит слова всех уровней",
    "qmode_category_set": "✅ Режим: {category}",

    # Названия категорий
    "cat_arbeit_beruf": "Работа",
    "cat_bildung_lernen": "Учёба",
    "cat_einkaufen_geld": "Покупки",
    "cat_emotionen_charakter": "Эмоции",
    "cat_essen_trinken": "Еда",
    "cat_freizeit_sport": "Спорт",
    "cat_gesundheit_medizin": "Здоровье",
    "cat_grammatik": "Грамматика",
    "cat_kleidung_mode": "Одежда",
    "cat_kommunikation": "Общение",
    "cat_kultur_kunst": "Культура",
    "cat_mensch_familie": "Семья",
    "cat_natur_wetter": "Природа",
    "cat_recht_staat": "Право",
    "cat_reisen_transport": "Путешествия",
    "cat_technik_digital": "Технологии",
    "cat_wirtschaft": "Экономика",
    "cat_wissenschaft": "Наука",
    "cat_wohnen_haus": "Жильё",
    "cat_zeit_alltag": "Быт",

    "qmode_all_set": "✅ Режим: Топ 10 тысяч",

    "qmode_difficult_set": "✅ Режим: Сложные слова",
    "qmode_difficult_few": "У тебя пока только {count} сложных слов — нужно минимум 4\nПройди ещё несколько викторин!",
    "qmode_difficult_empty": "У тебя пока нет сложных слов.\nПройди несколько викторин!",

    "quiz_btn_change_mode": "⚙️ Режим викторины",
    "quiz_btn_report_error": "📝 Ошибка перевода",
    "report_btn_confirm": "✅ Подтвердить ({count})",
    "report_btn_send": "📨 Отправить",
    "report_no_words": "Нет слов для репорта",
    "report_none_selected": "Выбери хотя бы одно слово",
    "report_sent": "✅ Отправлено {count} репортов — спасибо!",

    # ============================================================================
    # ВИКТОРИНА
    # ============================================================================
    "quiz_no_level": "⚠️ Сначала выбери свой уровень с помощью команды /start",
    "quiz_error_generation": "❌ Произошла ошибка при подготовке викторины.\nПопробуйте ещё раз через /start",
    "quiz_no_words": "❌ К сожалению, для этого уровня пока нет слов.\nПопробуй выбрать другой уровень.",

    "quiz_question_number": "Вопрос {current}/{total}",
    "quiz_question_choose_word": "Выбери правильное слово:",
    "quiz_question_choose_translation": "Выбери правильный перевод:",

    "quiz_correct": "✅ <b>Правильно!</b>",
    "quiz_wrong": "❌ <b>Неправильно!</b>",
    "quiz_correct_answer": "Правильный ответ:",

    "quiz_btn_next": "Дальше →",
    "quiz_btn_repeat_errors": "🔄 Повторить ошибки",

    "quiz_completed": "🎉 <b>Викторина завершена!</b>",
    "quiz_result_correct": "✅ Правильно: <b>{correct}/{total}</b>",
    "quiz_result_percentage": "📈 Результат: <b>{percentage}%</b>",
    "quiz_result_details": "📝 <b>Детали:</b>",
    "quiz_result_errors": "❌ Ошибок: {count}",

    "quiz_repeat_title": "🔄 <b>Повтор ошибок</b>",
    "quiz_repeat_question": "🔄 Повтор {current}/{total}",
    "quiz_no_errors": "✅ У тебя не было ошибок!",
    "quiz_error_next": "❌ Не удалось загрузить следующий вопрос.",
    "quiz_error_generate": "❌ Не удалось сгенерировать следующий вопрос.",

    # ============================================================================
    # СТАТИСТИКА
    # ============================================================================
    "stats_title": "📊 <b>Статистика</b>",
    "stats_no_level": "⚠️ <b>Сначала выбери уровень!</b>\n\nИспользуй команду /start чтобы начать.",

    "stats_all_words": "📚 Вся база ({count} слово|слова|слов)",
    "stats_learned": "✅ Выучено: {count}",
    "stats_in_progress": "🔄 В процессе: {count}",
    "stats_new": "🆕 Новых: {count}",
    "stats_difficult": "❌ Сложные: {count}",

    "stats_level_title": "🎯 Уровень {level} · {mode} ({count} слово|слова|слов)",
    "stats_quizzes_title": "🏆 <b>Викторины (уровень {level}):</b>",
    "stats_quizzes_passed": "Пройдено: {count}",
    "stats_quizzes_avg": "Средний результат: {percentage}%",
    "stats_quizzes_best": "Лучший результат: {percentage}%",
    "stats_quizzes_none": "Ты ещё не проходил викторины на этом уровне.",

    "stats_activity_title": "🔥 <b>Активность:</b>",
    "stats_streak": "└─ Стрик: <b>{days}</b> дней подряд",

    "stats_recent_title": "<b>Последние викторины:</b>",
    "stats_learned_explanation": "💡 <b>Выучено</b> — 3 правильных ответа подряд по слову",

    # ============================================================================
    # ПОМОЩЬ
    # ============================================================================
    "help_title": "❓ <b>Помощь — GenauLingua</b>",
    "help_description": "Здесь ты найдёшь инструкции, узнаешь что скоро появится в боте и как связаться с сообществом.",
    "help_choose": "Выбери раздел:",

    "help_btn_how_to_use": "📖 Как пользоваться",
    "help_btn_roadmap": "🚀 Скоро в боте",
    "help_btn_community": "💬 Сообщество",
    "help_btn_about": "ℹ️ О боте",

    "help_how_to_use_title": "📖 <b>Как пользоваться ботом</b>",
    "help_how_to_use_text": """1️⃣ <b>Настрой уровень и режим</b>
🦾 Настройки → выбери уровень A1–C2, режим перевода и язык интерфейса.

2️⃣ <b>Выбери режим викторины</b>
🦾 Настройки → 📝 Режим викторины:
• По уровню — слова твоего уровня
• По категории — 20 тем: еда, работа, путешествия...
• Топ 10 тысяч — вся база слов
• Сложные — слова, в которых ты часто ошибаешься

3️⃣ <b>Учи слова каждый день</b>
📚 Учить слова → викторина из 25 слов.
Бот запоминает твои ошибки и чаще показывает сложные слова.

4️⃣ <b>Повторяй ошибки</b>
После викторины можешь сразу повторить слова, в которых ошибся.

5️⃣ <b>Следи за прогрессом</b>
📊 Статистика → сколько выучено, история викторин, стрик.

6️⃣ <b>Соревнуйся с другими</b>
🏆 Мой рейтинг → твои баллы за месяц и за всё время.
📊 Таблица лидеров → топ-10 среди всех участников.

7️⃣ <b>Настрой напоминания</b>
🦾 Настройки → 🔔 Напоминания → выбери время, дни и часовой пояс.

━━━━━━━━━━━━━━━━━
💡 Слово <b>выучено</b> — если ответил правильно 3 раза подряд.
🔥 <b>Стрик</b> растёт если прошёл хотя бы 1 викторину в этот день.
📝 Нашёл ошибку в переводе? Нажми кнопку после викторины.

Вопросы? → t.me/genaulingua_chat""",

    "help_roadmap_title": "🚀 <b>Скоро в GenauLingua</b>",
    "help_roadmap_text": """🏆 <b>Достижения</b>
Бейджи за прогресс — первая викторина, 7 дней подряд, 100 слов выучено, викторина на 100% и другие.

🎓 <b>Подготовка к экзаменам</b>
Режимы подготовки к Goethe/ÖSD экзаменам A2–B2. Тренировка лексики, которая встречается на экзаменах.

📖 <b>Работа с текстами</b>
Чтение и разбор текстов на немецком с переводом, новыми словами и заданиями.

📝 <b>Грамматика</b>
Интерактивные упражнения по грамматике — артикли, падежи, времена, порядок слов.

━━━━━━━━━━━━━━━━━
💬 Идеи и пожелания — пиши в чат:
t.me/genaulingua_chat""",

    "help_community_title": "💬 <b>Сообщество GenauLingua</b>",
    "help_community_text": """👉 <b>t.me/genaulingua_chat</b>

В чате:
📢 Первыми узнаёшь об обновлениях
🐛 Нашёл баг — пиши или присылай скриншот
📝 Ошибка в переводе — сообщай, исправим
💡 Идеи и пожелания — всё читаем и берём в работу
👥 Общение с другими учениками

━━━━━━━━━━━━━━━━━
Чем активнее сообщество — тем лучше становится бот. Не стесняйся! 🙌""",

    "help_about_title": "ℹ️ <b>О боте</b>",
    "help_about_text": """🤖 <b>GenauLingua</b> — персональный помощник в изучении немецкого.

✨ <b>Что умеет:</b>
• База слов A1–C2 (12 000+ слов)
• 20 тематических категорий
• 4 режима викторины: по уровню, по категории, топ 10К, сложные слова
• Умный подбор слов — SRS алгоритм
• 4 языка: DE↔RU, DE↔UA, DE↔EN, DE↔TR
• Повтор ошибок после викторины
• Сообщить об ошибке перевода прямо из викторины
• Статистика, стрик и прогресс-бар
• Месячный рейтинг и таблица лидеров
• Напоминания с гибким расписанием
• Интерфейс на русском, украинском, английском и турецком

📅 <b>Обновлено:</b> Апрель 2026

💬 Следи за обновлениями: t.me/genaulingua_chat""",

    # ============================================================================
    # РЕЙТИНГ
    # ============================================================================
    "rating_title_monthly": "🏆 <b>Мой рейтинг — {month} {year}</b>",
    "rating_not_active": "❌ Рейтинг пока не активен.",
    "rating_not_in_ranking": "📍 Ты ещё не в рейтинге",
    "rating_start_quiz": "🚀 Пройди первую викторину!",
    "rating_position": "📍 Позиция: <b>#{rank}</b> из {total}",
    "rating_points": "💎 Баллы: <b>{score}</b>",
    "rating_your_month": "⭐ <b>Твой {month}:</b>",
    "rating_quizzes": "├ Викторин: {count}",
    "rating_words_learned": "├ Выучено слов: {count}",
    "rating_streak": "├ Стрик: {count} дн.",
    "rating_avg_result": "└ Средний результат: {percent}%",
    "rating_goal": "🎯 До #{rank} ({name}): ещё {diff} баллов",
    "rating_scoring_title": "💡 <b>Как заработать баллы:</b>",
    "rating_scoring_quiz": "• Пройденная викторина → +10",
    "rating_scoring_reverse": "• Режим «Реверс» → +5",
    "rating_scoring_word": "• Выученное слово → +2",
    "rating_scoring_streak": "• День подряд → +3",
    "rating_scoring_bonus": "• Точность 90%+ → +50 бонус",

    "rating_title_alltime": "🏆 <b>Мой рейтинг — За всё время</b>",
    "rating_position_alltime": "📍 Позиция: <b>#{rank}</b>",
    "rating_position_none": "📍 Позиция: <b>—</b>",
    "rating_achievements": "⭐ <b>Твои достижения:</b>",
    "rating_wins": "├ Побед (1 место): {count}",
    "rating_total_words": "└ Выучено слов: {count}",
    "rating_motivation_start": "🚀 Начни учить слова — первый шаг самый важный!",
    "rating_motivation_continue": "🎯 Продолжай — первая победа уже близко!",
    "rating_motivation_champion": "🔥 Ты настоящий чемпион!",
    "rating_lifetime_title": "🌟 <b>Lifetime баллы — это:</b>",
    "rating_lifetime_desc": "• Все баллы за все месяцы\n• +100 за 🥇 · +50 за 🥈 · +25 за 🥉",

    "table_title_monthly": "📊 <b>Таблица лидеров — {month} {year}</b>",
    "table_title_alltime": "📊 <b>Таблица лидеров — За всё время</b>",
    "table_empty": "Пока никто не участвует.\nПройди викторину первым! 💪",
    "table_you_in_top": "📍 Ты: <b>#{rank}</b> из {total}",
    "table_you_not_in_top": "📍 Ты: <b>#{rank}</b> из {total} — {score} баллов",
    "table_you_outside": "📍 Ты: за пределами топ-10 — {score} баллов",
    "table_you_not_ranked": "📍 Ты ещё не в рейтинге",
    "table_points": "баллов",
    "btn_leaderboard_table": "📊 Таблица лидеров",
    "btn_back_to_rating": "◀️ Назад к рейтингу",

    # ============================================================================
    # СТАТИСТИКА (НОВАЯ)
    # ============================================================================
    "stats_header": "📊 <b>Твоя статистика</b>",
    "stats_learned_of": "└─ Выучено <b>{learned}</b> из {total}",
    "stats_details": "⏳ В процессе: {progress}\n🆕 Новых: {new}\n⚠️ Сложных: {difficult}",
    "stats_achievements_title": "<b>Твои достижения</b>",
    "stats_words_count": "├─ Выучено слов: <b>{count}</b>",
    "stats_streak_line": "└─ Стрик: <b>{days} дней подряд</b>",
    "stats_quizzes_header": "<b>Викторины · {level}</b>",
    "stats_quizzes_passed_line": "├─ Пройдено: <b>{count}</b>",
    "stats_quizzes_avg_line": "├─ Средний результат: <b>{percent}%</b>",
    "stats_quizzes_best_line": "└─ Лучший результат: <b>{percent}%</b>",
    "stats_quizzes_empty": "└─ Пока нет пройденных викторин",
    "stats_recent_header": "📈 <b>Последние викторины</b>",
    "stats_overall_header": "🌍 <b>Общий прогресс</b>",
    "stats_overall_learned": "└─ Выучено <b>{learned}</b> из {total} слов",
    "stats_cta_start": "💪 Начни учить слова — первый шаг самый важный!",
    "stats_cta_begin": "🚀 Отличное начало! Продолжай в том же духе!",
    "stats_cta_halfway": "🔥 Ты на полпути! Не останавливайся!",
    "stats_cta_almost": "🏆 Почти у цели! Ты молодец!",
    "stats_explanation": "—————————————————————\nСлово выучено = 3 правильных ответа подряд",
    "stats_btn_rating": "🏆 Мой рейтинг",
}