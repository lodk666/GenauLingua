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
    "welcome_description": "🇩🇪 <b>GenauLingua</b> — learn German every day.\nThe bot analyzes your results and picks words just for you.",
    "welcome_separator": "──────────────────",

    "welcome_learn_words_title": "📚 <b>Learn words</b>",
    "welcome_learn_words_desc": "Fun quizzes with German words. The more you practice — the smarter the word selection.",

    "welcome_stats_title": "📊 <b>Statistics</b>",
    "welcome_stats_desc": "Progress by level, quiz history, comparison with other users.",

    "welcome_settings_title": "🦾 <b>Settings</b>",
    "welcome_settings_desc": "Level (A1–C2), interface language, quiz mode.",

    "welcome_help_title": "❓ <b>Help</b>",
    "welcome_help_desc": "Tips, latest updates and feedback.",

    "welcome_your_level": "Your level: <b>{level}</b> · Mode: <b>{mode}</b>",
    "welcome_call_to_action": "Tap 📚 Learn words — let's go!",

    "welcome_choose_level": "First, choose your German level:",
    "choose_level_prompt": "Choose your level:",

    "level_selected": "✅ Level <b>{level}</b> selected.\n\nTap 📚 Learn words — let's go!",
    "level_locked": "🔒 This level is coming soon",

    # ============================================================================
    # SETTINGS
    # ============================================================================
    "settings_title": "🦾 <b>Settings</b>",
    "settings_level": "📚 Level: <b>{level}</b>",
    "settings_mode": "🔄 Mode: <b>{mode}</b>",
    "settings_language": "🌍 Interface language: <b>{language}</b>",
    "settings_choose": "Choose what you want to change:",

    "settings_btn_change_level": "📚 Change level",
    "settings_btn_change_mode": "🔄 Translation mode",
    "settings_btn_change_language": "🌍 Interface language",

    "settings_level_title": "📚 <b>Choose level</b>",
    "settings_level_description": "Choose your current German level:\n\n• <b>A1</b> — Beginner (Hello, how are you?)\n• <b>A2</b> — Elementary (Simple dialogues)\n• <b>B1</b> — Intermediate (Everyday communication)",

    "settings_mode_title": "🔄 <b>Translation mode</b>",
    "settings_mode_description": "Choose translation direction:",

    "settings_language_title": "🌍 <b>Interface language</b>",
    "settings_language_description": "Choose the bot interface language:",

    "language_changed": "✅ Language changed to {language}",
    "level_not_selected": "Not selected",
    "user_not_found": "❌ User not found. Use /start",

    # Language names
    "lang_ru": "🏴 Русский",
    "lang_uk": "🇺🇦 Українська",
    "lang_en": "🇬🇧 English",
    "lang_tr": "🇹🇷 Türkçe",

    # Translation modes
    "mode_de_to_ru": "🇩🇪 DE → 🏴 RU",
    "mode_ru_to_de": "🏴 RU → 🇩🇪 DE",
    "mode_de_to_uk": "🇩🇪 DE → 🇺🇦 UK",
    "mode_uk_to_de": "🇺🇦 UK → 🇩🇪 DE",
    "mode_de_to_en": "🇩🇪 DE → 🇬🇧 EN",
    "mode_en_to_de": "🇬🇧 EN → 🇩🇪 DE",
    "mode_de_to_tr": "🇩🇪 DE → 🇹🇷 TR",
    "mode_tr_to_de": "🇹🇷 TR → 🇩🇪 DE",

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
🦾 Settings → choose level A1–B1, translation mode and language.

2️⃣ <b>Learn words every day</b>
📚 Learn words → quiz with 25 words.
The bot remembers your mistakes and shows difficult words more often.

3️⃣ <b>Repeat your mistakes</b>
After the quiz you can immediately repeat the words you got wrong.

4️⃣ <b>Track your progress</b>
📊 Statistics → how many learned, quiz history, streak.

━━━━━━━━━━━━━━━━━
💡 A word is <b>learned</b> when you answer correctly 3 times in a row.
🔥 <b>Streak</b> grows if you complete at least 1 quiz per day.

Questions? → t.me/genaulingua_chat""",

    "help_roadmap_title": "🚀 <b>Coming soon to GenauLingua</b>",
    "help_roadmap_text": """🏆 <b>Achievements</b>
Badges for progress — first quiz, 7 days in a row, 100 words learned, 100% quiz and more.

🥇 <b>Leaderboard</b>
Rankings among all users — by words, streak and quiz results.

🎯 <b>Challenges</b>
Weekly tasks — complete 7 quizzes in a row, learn 100 words in a week, score 90%+ three times.

🔔 <b>Reminders</b>
Set a time — the bot will remind you to practice and show your current streak.

📚 <b>Levels B2–C2</b>
Currently A1–B1 available. B2, C1 and C2 are in progress.

🎤 <b>Pronunciation</b>
Word audio — listen to how German words sound.

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

✨ <b>Current features:</b>
• Word base A1–B1 (3000+ words)
• Smart word selection — SRS algorithm
• Modes DE→EN, EN→DE, DE→RU, DE→UA
• Repeat mistakes after quiz
• Statistics and streak
• Interface in English, Russian, Ukrainian, Turkish

📅 <b>Updated:</b> February 2026

💬 Follow updates: t.me/genaulingua_chat""",
}