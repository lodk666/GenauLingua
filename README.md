# GenauLingua

**Telegram bot for learning German vocabulary** — from A1 to C2, with adaptive spaced repetition, statistics, and gamification.

[@GenauLinguaBot](https://t.me/GenauLinguaBot)

---

## Project Status

> **MVP complete.** The bot is live, free, and open to everyone.  
> Active development is paused — the project is maintained in its current state.

### Live Stats (June 2026)

| Metric | Value |
|---|---|
| Registered users | 198 |
| Completed at least 1 quiz | 109 (55%) |
| Active core | ~10–15 users |
| Total quizzes completed | 1,423 |
| Word database | 12,805 words (A1–C2) |
| Interface languages | 🇷🇺 RU · 🇺🇦 UK · 🇬🇧 EN · 🇹🇷 TR |

---

## Features

### Adaptive Learning (SRS)
Individual repetition intervals per word. Weak and frequently mistaken words appear more often, mastered ones less. Difficulty adjusts based on performance.

### Word Database
12,805 words across levels A1–C2, organized into 21 thematic categories. Each word includes a translation and example sentence in 4 languages (RU, UK, EN, TR), with part of speech, article, and frequency rank.

### Quizzes
25-word sessions, 4 answer options, instant feedback with the correct answer and an example sentence. Error repetition mode after completion. Smart distractor selection (same POS, different article).

### Multi-Language Support
4 interface languages, 4 translation modes (DE↔RU, DE↔UA, DE↔EN, DE↔TR), reverse mode for advanced learners. Full localization of all UI elements.

### Leaderboard & Rating
Monthly and all-time rating system. Top-10 leaderboard, automatic season reset, streaks, achievements. Scoring: quizzes (+10), reverse mode (+5), words learned (+2), streak days (+3), accuracy bonuses.

### Reminders
Customizable reminder time and days, 20+ timezone support, motivational messages with progress stats.

### User Statistics
Progress bar per level and overall, quiz history with results, word breakdown (learned / in progress / difficult), streak tracking, achievement system.

### Admin Panel
Analytics dashboard, cohort analysis, churn detection, CSV export, localized broadcast messaging, per-user detailed statistics.

---

## Tech Stack

| | |
|---|---|
| Language | Python 3.11 |
| Telegram API | aiogram 3.15 |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Scheduler | APScheduler |
| Deployment | Docker / Docker Compose |

---

## Getting Started

```bash
git clone https://github.com/lodk666/GenauLingua.git
cd GenauLingua
cp .env.example .env  # fill in your variables
docker compose up -d --build
```

Migrations are applied automatically on container startup.

---

## Configuration

All secrets (bot token, database credentials, admin IDs) are provided via environment variables. No secrets are stored in the repository.

---

## Privacy

[PRIVACY_POLICY.md](https://github.com/lodk666/GenauLingua/blob/main/PRIVACY_POLICY.md)

---

## License

This project was built as a personal learning project. The bot is free and runs without ads.
