"""
English localization for GenauLingua Bot
"""

TEXTS = {
    # ============================================================================
    # MAIN MENU BUTTONS
    # ============================================================================
    "btn_learn_words": "📚 Learn words",
    "btn_stats": "📊 Statistics",
    "btn_settings": "🦾 Settings",
    "btn_help": "❓ Help",
    "btn_back": "◀️ Back",
    "menu_placeholder": "Choose an action...",

    # ============================================================================
    # WELCOME & START
    # ============================================================================
    "welcome_title": "👋 <b>Hello, {name}!</b>",
    "welcome_description": "🇩🇪 <b>GenauLingua</b> — learn German through play\n12 000+ words · 20 topics · 6 levels\n\nThe bot picks words just for you — the more\nyou play, the smarter the selection",
    "welcome_separator": "──────────────────",

    "welcome_learn_words_title": "📚 <b>Learn words</b>",
    "welcome_learn_words_desc": "Start a quiz",

    "welcome_stats_title": "📊 <b>Statistics</b>",
    "welcome_stats_desc": "Your progress",

    "welcome_settings_title": "🦾 <b>Settings</b>",
    "welcome_settings_desc": "Mode, language, topics",

    "welcome_help_title": "❓ <b>Help</b>",
    "welcome_help_desc": "Tips and feedback",

    "welcome_your_level": "Your level: <b>{level}</b>\nMode: <b>{mode}</b>",
    "welcome_call_to_action": "Tap 📚 Learn words — let's go!",

    "welcome_choose_level": "🎯 <b>Where do we start?</b>\n\nChoose your German level\n\n• A1–A2 — basic vocabulary\n• B1–B2 — confident communication\n• C1–C2 — near-native fluency",
    "choose_level_prompt": "Choose your level:",

    "level_selected": "✅ Level <b>{level}</b> selected.\n\nTap 📚 Learn words — let's go!",
    "level_locked": "🔒 This level is coming soon",

    # ============================================================================
    # NOTIFICATIONS
    # ============================================================================
    "notif_title": "🔔 <b>Notification Settings</b>",
    "notif_status": "Status: {status}",
    "notif_status_on": "🔔 Enabled",
    "notif_status_off": "🔕 Disabled",
    "notif_time": "Time: {time}",
    "notif_days": "Days: {days}",
    "notif_timezone": "Timezone: {timezone}",
    "notif_hint": "💡 Notifications will arrive at the specified time in your timezone.",
    "notif_hint_off": "💡 Enable notifications to never forget your daily practice!",

    "notif_btn_toggle_on": "🔔 Notifications: Enabled",
    "notif_btn_toggle_off": "🔕 Notifications: Disabled",
    "notif_btn_time": "🕐 Time: {time}",
    "notif_btn_days": "📅 Select days",
    "notif_btn_timezone": "🌍 Change timezone",

    "notif_timezone_title": "🌍 <b>Select your timezone</b>",
    "notif_timezone_current": "Current: {timezone}",
    "notif_timezone_prompt": "Select a city in your timezone:",
    "notif_timezone_more": "🌍 Select another city ▼",
    "notif_timezone_back": "◀️ Back",
    "notif_timezone_set": "✅ Timezone set: {city}",

    "notif_time_title": "🕐 <b>Select notification time</b>",
    "notif_time_current": "Current time: {time}",
    "notif_time_timezone": "Timezone: {timezone}",
    "notif_time_hint": "Notification will arrive daily at the selected time.",
    "notif_time_set": "✅ Time set: {time}",

    "notif_days_title": "📅 <b>Select notification days</b>",
    "notif_days_hint": "Tap on a day to enable/disable it.\n✅ Green check - day enabled\n❌ Red cross - day disabled\n\nWhen done - tap 'Save'.",
    "notif_days_all": "📅 All days",
    "notif_days_weekdays": "🗓️ Weekdays (Mon-Fri)",
    "notif_days_save": "💾 Save",
    "notif_days_saved": "✅ Days saved!",
    "notif_days_all_selected": "✅ All days selected",
    "notif_days_weekdays_selected": "✅ Weekdays selected (Mon-Fri)",
    "notif_days_none": "⚠️ Select at least one day for notifications!",

    "notif_toggle_on": "🔔 Notifications enabled!",
    "notif_toggle_off": "🔕 Notifications disabled",

    "notif_message_title": "{emoji} <b>Time to practice!</b>",
    "notif_message_streak": "🔥 Streak: {days} days",
    "notif_message_words": "📊 Words learned: {count}",
    "notif_message_cta": "💪 Keep your streak going!",
    "notif_message_btn_start": "📚 Start quiz",
    "notif_message_btn_disable": "🔕 Disable notifications",

    "day_mon": "Mon",
    "day_tue": "Tue",
    "day_wed": "Wed",
    "day_thu": "Thu",
    "day_fri": "Fri",
    "day_sat": "Sat",
    "day_sun": "Sun",

    "notif_btn_back": "◀️ Back to settings",

    "notif_default_name": "friend",
    "notif_message_greeting": "🔥 <b>Time to practice, {name}!</b>",
    "notif_message_progress_title": "📊 <b>Your progress:</b>",
    "notif_progress_streak": "├ Streak: {days} days 🎯",
    "notif_progress_quizzes": "├ Quizzes passed: {count}",
    "notif_progress_words": "├ Words learned: {count}",
    "notif_progress_accuracy": "└ Accuracy: {percent}%",

    "notif_motivation_1": "Step by step you're reaching your goal!",
    "notif_motivation_2": "Your streak is growing — keep it up!",
    "notif_motivation_3": "Today is another step toward fluent German!",
    "notif_motivation_4": "Small efforts every day = big results!",
    "notif_motivation_5": "You're on the right path! Don't stop!",
    "notif_motivation_6": "Each quiz brings you closer to your goal!",

    # ============================================================================
    # SETTINGS
    # ============================================================================
    "settings_title": "🦾 <b>Settings</b>",
    "settings_level": "📚 Level: <b>{level}</b>",
    "settings_mode": "🔄 Translation: <b>{mode}</b>",
    "settings_language": "🌍 Interface language: <b>{language}</b>",
    "settings_choose": "Choose what you want to change:",

    "settings_btn_quiz_mode": "📝 Quiz mode",
    "settings_btn_change_mode": "🔄 Translation mode",
    "settings_btn_change_language": "🌍 Interface language",
    "settings_btn_notifications": "🔔 Notifications",

    "settings_quiz_mode_line": "📝 Mode: <b>{mode}</b>",

    "settings_mode_title": "🔄 <b>Translation mode</b>",
    "settings_mode_description": "Choose translation direction:",

    "settings_language_title": "🌍 <b>Interface language</b>",
    "settings_language_description": "Choose the bot interface language:",

    "language_changed": "✅ Language changed to {language}",
    "level_not_selected": "Not selected",
    "user_not_found": "❌ User not found. Use /start",

    "lang_ru": "🏴 Русский",
    "lang_uk": "🇺🇦 Українська",
    "lang_en": "🇬🇧 English",
    "lang_tr": "🇹🇷 Türkçe",

    "mode_de_to_ru": "🇩🇪 DE → 🏴 RU",
    "mode_ru_to_de": "🏴 RU → 🇩🇪 DE",
    "mode_de_to_uk": "🇩🇪 DE → 🇺🇦 UK",
    "mode_uk_to_de": "🇺🇦 UK → 🇩🇪 DE",
    "mode_de_to_en": "🇩🇪 DE → 🇬🇧 EN",
    "mode_en_to_de": "🇬🇧 EN → 🇩🇪 DE",
    "mode_de_to_tr": "🇩🇪 DE → 🇹🇷 TR",
    "mode_tr_to_de": "🇹🇷 TR → 🇩🇪 DE",

    "settings_mode_hint_de_en": "💡 DE→EN easier — you can guess from context",
    "settings_mode_hint_en_de": "💡 EN→DE harder — better memorization",
    "settings_mode_hint_de_ru": "💡 DE→RU easier — you can guess from context",
    "settings_mode_hint_ru_de": "💡 RU→DE harder — better memorization",
    "settings_mode_hint_de_uk": "💡 DE→UK easier — you can guess from context",
    "settings_mode_hint_uk_de": "💡 UK→DE harder — better memorization",
    "settings_mode_hint_de_tr": "💡 DE→TR easier — you can guess from context",
    "settings_mode_hint_tr_de": "💡 TR→DE harder — better memorization",

    # ============================================================================
    # QUIZ MODE (NEW)
    # ============================================================================
    "qmode_title": "📝 <b>Quiz mode</b>",
    "qmode_current": "Current: <b>{mode}</b>",
    "qmode_choose": "Choose how you want to learn\nYou can switch anytime — your progress is saved",

    "qmode_btn_level": "📚 By level",
    "qmode_btn_category": "🗂 Category",
    "qmode_btn_all": "🌍 Top 10 thousand",
    "qmode_btn_difficult": "⚠️ Difficult",

    "qmode_level_short": "📚 Level {level}",
    "qmode_category_short": "🗂 {category}",
    "qmode_all_short": "🌍 Top 10 thousand",
    "qmode_difficult_short": "⚠️ Difficult words",

    "qmode_level_title": "📚 <b>Choose level</b>",
    "qmode_level_desc": "From your first «Hallo» to fluent debates\nAll levels available — pick yours!\n\n• A1–A2 — basic vocabulary\n• B1–B2 — confident communication\n• C1–C2 — near-native fluency",
    "qmode_level_set": "✅ Mode: By level ({level})",

    "qmode_category_title": "🗂 <b>Choose category</b>",
    "qmode_category_desc": "From food to science — pick the topic you need\n\nEach category includes words from all levels",
    "qmode_category_set": "✅ Mode: {category}",

    # Category names
    "cat_arbeit_beruf": "Work",
    "cat_bildung_lernen": "Education",
    "cat_einkaufen_geld": "Shopping",
    "cat_emotionen_charakter": "Emotions",
    "cat_essen_trinken": "Food",
    "cat_freizeit_sport": "Sports",
    "cat_gesundheit_medizin": "Health",
    "cat_grammatik": "Grammar",
    "cat_kleidung_mode": "Fashion",
    "cat_kommunikation": "Communication",
    "cat_kultur_kunst": "Culture",
    "cat_mensch_familie": "Family",
    "cat_natur_wetter": "Nature",
    "cat_recht_staat": "Law",
    "cat_reisen_transport": "Travel",
    "cat_technik_digital": "Technology",
    "cat_wirtschaft": "Economy",
    "cat_wissenschaft": "Science",
    "cat_wohnen_haus": "Housing",
    "cat_zeit_alltag": "Daily life",

    "qmode_all_set": "✅ Mode: Top 10 thousand",

    "qmode_difficult_set": "✅ Mode: Difficult words",
    "qmode_difficult_few": "You only have {count} difficult words — need at least 4\nTake a few more quizzes!",
    "qmode_difficult_empty": "You don't have difficult words yet.\nTake a few quizzes first!",

    "quiz_btn_change_mode": "⚙️ Quiz mode",
    "quiz_btn_report_error": "📝 Translation error",
    "report_btn_confirm": "✅ Confirm ({count})",
    "report_btn_send": "📨 Send",
    "report_no_words": "No words to report",
    "report_none_selected": "Select at least one word",
    "report_sent": "✅ Sent {count} reports — thank you!",

    # ============================================================================
    # QUIZ
    # ============================================================================
    "quiz_no_level": "⚠️ First choose your level using /start",
    "quiz_error_generation": "❌ An error occurred while preparing the quiz.\nTry again via /start",
    "quiz_no_words": "❌ Sorry, no words available for this level.\nTry choosing a different level.",

    "quiz_question_number": "Question {current}/{total}",
    "quiz_question_choose_word": "Choose the correct word:",
    "quiz_question_choose_translation": "Choose the correct translation:",

    "quiz_correct": "✅ <b>Correct!</b>",
    "quiz_wrong": "❌ <b>Wrong!</b>",
    "quiz_correct_answer": "Correct answer:",

    "quiz_btn_next": "Next →",
    "quiz_btn_repeat_errors": "🔄 Repeat mistakes",

    "quiz_completed": "🎉 <b>Quiz completed!</b>",
    "quiz_result_correct": "✅ Correct: <b>{correct}/{total}</b>",
    "quiz_result_percentage": "📈 Result: <b>{percentage}%</b>",
    "quiz_result_details": "📝 <b>Details:</b>",
    "quiz_result_errors": "❌ Mistakes: {count}",

    "quiz_repeat_title": "🔄 <b>Repeat mistakes</b>",
    "quiz_repeat_question": "🔄 Repeat {current}/{total}",
    "quiz_no_errors": "✅ You had no mistakes!",
    "quiz_error_next": "❌ Failed to load next question.",
    "quiz_error_generate": "❌ Failed to generate next question.",

    # ============================================================================
    # STATISTICS
    # ============================================================================
    "stats_title": "📊 <b>Statistics</b>",
    "stats_no_level": "⚠️ <b>Choose your level first!</b>\n\nUse /start to begin.",

    "stats_all_words": "📚 All words ({count})",
    "stats_learned": "✅ Learned: {count}",
    "stats_in_progress": "🔄 In progress: {count}",
    "stats_new": "🆕 New: {count}",
    "stats_difficult": "❌ Difficult: {count}",

    "stats_level_title": "🎯 Level {level} · {mode} ({count} words)",
    "stats_quizzes_title": "🏆 <b>Quizzes (level {level}):</b>",
    "stats_quizzes_passed": "Completed: {count}",
    "stats_quizzes_avg": "Average result: {percentage}%",
    "stats_quizzes_best": "Best result: {percentage}%",
    "stats_quizzes_none": "You haven't taken any quizzes at this level yet.",

    "stats_activity_title": "🔥 <b>Activity:</b>",
    "stats_streak": "└─ Streak: <b>{days}</b> days in a row",

    "stats_recent_title": "<b>Recent quizzes:</b>",
    "stats_learned_explanation": "💡 <b>Learned</b> — 3 correct answers in a row for a word",

    # ============================================================================
    # HELP
    # ============================================================================
    "help_title": "❓ <b>Help — GenauLingua</b>",
    "help_description": "Here you'll find instructions, upcoming features and how to reach the community.",
    "help_choose": "Choose a section:",

    "help_btn_how_to_use": "📖 How to use",
    "help_btn_roadmap": "🚀 Coming soon",
    "help_btn_community": "💬 Community",
    "help_btn_about": "ℹ️ About",

    "help_how_to_use_title": "📖 <b>How to use the bot</b>",
    "help_how_to_use_text": """1️⃣ <b>Set your level and mode</b>
🦾 Settings → choose level A1–C2, translation mode and interface language.

2️⃣ <b>Choose quiz mode</b>
🦾 Settings → 📝 Quiz mode:
• By level — words from your level
• By category — 20 topics: food, work, travel...
• Top 10 thousand — entire word base
• Difficult — words you often get wrong

3️⃣ <b>Learn words every day</b>
📚 Learn words → quiz with 25 words.
The bot remembers your mistakes and shows difficult words more often.

4️⃣ <b>Repeat your mistakes</b>
After the quiz you can immediately repeat the words you got wrong.

5️⃣ <b>Track your progress</b>
📊 Statistics → how many learned, quiz history, streak.

6️⃣ <b>Compete with others</b>
🏆 My rating → your monthly and all-time points.
📊 Leaderboard → top-10 among all participants.

7️⃣ <b>Set up reminders</b>
🦾 Settings → 🔔 Notifications → choose time, days and timezone.

━━━━━━━━━━━━━━━━━
💡 A word is <b>learned</b> when you answer correctly 3 times in a row.
🔥 <b>Streak</b> grows if you complete at least 1 quiz per day.
📝 Found a translation error? Tap the button after the quiz.

Questions? → t.me/genaulingua_chat""",

    "help_roadmap_title": "🚀 <b>Coming soon to GenauLingua</b>",
    "help_roadmap_text": """🏆 <b>Achievements</b>
Badges for progress — first quiz, 7 days in a row, 100 words learned, 100% quiz and more.

🎓 <b>Exam preparation</b>
Preparation modes for Goethe/ÖSD exams A2–B2. Practice vocabulary that appears on exams.

📖 <b>Reading practice</b>
Read and analyze German texts with translations, new words and exercises.

📝 <b>Grammar</b>
Interactive grammar exercises — articles, cases, tenses, word order.

━━━━━━━━━━━━━━━━━
💬 Ideas and suggestions — write in chat:
t.me/genaulingua_chat""",

    "help_community_title": "💬 <b>GenauLingua Community</b>",
    "help_community_text": """👉 <b>t.me/genaulingua_chat</b>

In the chat:
📢 Be the first to know about updates
🐛 Found a bug — write or send a screenshot
📝 Translation error — report it, we'll fix it
💡 Ideas and suggestions — we read everything
👥 Chat with other learners

━━━━━━━━━━━━━━━━━
The more active the community — the better the bot gets. Don't be shy! 🙌""",

    "help_about_title": "ℹ️ <b>About the bot</b>",
    "help_about_text": """🤖 <b>GenauLingua</b> — your personal German learning assistant.

✨ <b>Features:</b>
• Word base A1–C2 (12,000+ words)
• 20 thematic categories
• 4 quiz modes: by level, by category, top 10K, difficult words
• Smart word selection — SRS algorithm
• 4 languages: DE↔RU, DE↔UA, DE↔EN, DE↔TR
• Repeat mistakes after quiz
• Report translation errors directly from quiz
• Statistics, streak and progress bar
• Monthly rating and leaderboard
• Flexible notification reminders
• Interface in English, Russian, Ukrainian, Turkish

📅 <b>Updated:</b> April 2026

💬 Follow updates: t.me/genaulingua_chat""",

    # ============================================================================
    # RATING
    # ============================================================================
    "rating_title_monthly": "🏆 <b>My rating — {month} {year}</b>",
    "rating_not_active": "❌ Rating is not active yet.",
    "rating_not_in_ranking": "📍 You're not in the ranking yet",
    "rating_start_quiz": "🚀 Take your first quiz!",
    "rating_position": "📍 Position: <b>#{rank}</b> of {total}",
    "rating_points": "💎 Points: <b>{score}</b>",
    "rating_your_month": "⭐ <b>Your {month}:</b>",
    "rating_quizzes": "├ Quizzes: {count}",
    "rating_words_learned": "├ Words learned: {count}",
    "rating_streak": "├ Streak: {count} days",
    "rating_avg_result": "└ Average result: {percent}%",
    "rating_goal": "🎯 To #{rank} ({name}): {diff} more points",
    "rating_scoring_title": "💡 <b>How to earn points:</b>",
    "rating_scoring_quiz": "• Completed quiz → +10",
    "rating_scoring_reverse": "• Reverse mode → +5",
    "rating_scoring_word": "• Word learned → +2",
    "rating_scoring_streak": "• Day streak → +3",
    "rating_scoring_bonus": "• 90%+ accuracy → +50 bonus",

    "rating_title_alltime": "🏆 <b>My rating — All Time</b>",
    "rating_position_alltime": "📍 Position: <b>#{rank}</b>",
    "rating_position_none": "📍 Position: <b>—</b>",
    "rating_achievements": "⭐ <b>Your achievements:</b>",
    "rating_wins": "├ Wins (1st place): {count}",
    "rating_total_words": "└ Words learned: {count}",
    "rating_motivation_start": "🚀 Start learning — the first step is the most important!",
    "rating_motivation_continue": "🎯 Keep going — your first win is near!",
    "rating_motivation_champion": "🔥 You're a true champion!",
    "rating_lifetime_title": "🌟 <b>Lifetime points:</b>",
    "rating_lifetime_desc": "• All points from all months\n• +100 for 🥇 · +50 for 🥈 · +25 for 🥉",

    "table_title_monthly": "📊 <b>Leaderboard — {month} {year}</b>",
    "table_title_alltime": "📊 <b>Leaderboard — All Time</b>",
    "table_empty": "No participants yet.\nBe the first to take a quiz! 💪",
    "table_you_in_top": "📍 You: <b>#{rank}</b> of {total}",
    "table_you_not_in_top": "📍 You: <b>#{rank}</b> of {total} — {score} points",
    "table_you_outside": "📍 You: outside top-10 — {score} points",
    "table_you_not_ranked": "📍 You're not ranked yet",
    "table_points": "points",
    "btn_leaderboard_table": "📊 Leaderboard",
    "btn_back_to_rating": "◀️ Back to rating",

    "stats_header": "📊 <b>Your statistics</b>",
    "stats_learned_of": "└─ Learned <b>{learned}</b> of {total}",
    "stats_details": "⏳ In progress: {progress}\n🆕 New: {new}\n⚠️ Difficult: {difficult}",
    "stats_achievements_title": "<b>Your achievements</b>",
    "stats_words_count": "├─ Words learned: <b>{count}</b>",
    "stats_streak_line": "└─ Streak: <b>{days} days in a row</b>",
    "stats_quizzes_header": "<b>Quizzes · {level}</b>",
    "stats_quizzes_passed_line": "├─ Completed: <b>{count}</b>",
    "stats_quizzes_avg_line": "├─ Average result: <b>{percent}%</b>",
    "stats_quizzes_best_line": "└─ Best result: <b>{percent}%</b>",
    "stats_quizzes_empty": "└─ No quizzes completed yet",
    "stats_recent_header": "📈 <b>Recent quizzes</b>",
    "stats_overall_header": "🌍 <b>Overall progress</b>",
    "stats_overall_learned": "└─ Learned <b>{learned}</b> of {total} words",
    "stats_cta_start": "💪 Start learning — the first step is the most important!",
    "stats_cta_begin": "🚀 Great start! Keep going!",
    "stats_cta_halfway": "🔥 Halfway there! Don't stop!",
    "stats_cta_almost": "🏆 Almost there! Great job!",
    "stats_explanation": "—————————————————————\nWord learned = 3 correct answers in a row",
    "stats_btn_rating": "🏆 My rating",
}