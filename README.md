# GenauLingua — German Vocabulary Learning Bot

**A production Telegram bot for learning German vocabulary (A1–C2)** with an adaptive
spaced-repetition engine, gamification, multi-language UI, and an admin analytics panel.

🤖 **Live bot:** [t.me/GenauLingua_bot](https://t.me/GenauLingua_bot)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![aiogram](https://img.shields.io/badge/aiogram-3.15-2CA5E0?logo=telegram&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%20async-D71F00)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

---

## Overview

GenauLingua is a fully deployed, real-world Telegram bot that teaches German vocabulary
using a personalized spaced-repetition system (SRS). It has been running in production,
serving real users, with a curated database of **12,805 words** across CEFR levels A1–C2.

The project is a complete, end-to-end product: data pipeline, async backend, database
design and migrations, gamification systems, background schedulers, full internationalization,
an admin analytics dashboard, and containerized deployment.

### Results in production

| Metric | Value |
|---|---|
| Registered users | 204 |
| Users who completed ≥1 quiz | 116 (57%) |
| Total quizzes completed | 1,570 |
| Word database | 12,805 words (A1–C2) |
| Interface languages | 🇷🇺 RU · 🇺🇦 UK · 🇬🇧 EN · 🇹🇷 TR |
| Uptime | Deployed on Hetzner (EU) via Docker |

> **Status:** MVP complete. The bot is live, free, and open to everyone. Active feature
> development is paused; the project is maintained in its current state.

---

## Key Features

**Adaptive spaced repetition (SRS).** Each word carries an individual repetition interval per
user. Weak and frequently-missed words resurface more often; mastered words fade out. Difficulty
adapts continuously to performance.

**Curated word database.** 12,805 words across A1–C2, organized into 21 thematic categories.
Every word ships with a translation and an example sentence in 4 languages (RU/UK/EN/TR), plus
part of speech, article, and frequency rank.

**Smart quizzes.** 25-word sessions with 4 answer options and instant feedback (correct answer +
example sentence). Distractors are chosen intelligently (same part of speech, different article).
Mistake-repetition mode replays missed words after each session.

**Multi-language & multi-mode.** 4 interface languages, 4 translation directions
(DE↔RU, DE↔UK, DE↔EN, DE↔TR), and a reverse mode for advanced learners. Every UI string is
fully localized.

**Gamification.** Monthly and all-time leaderboards, top-10 rankings, automatic season resets,
win streaks, achievements, and a transparent scoring system (quizzes, reverse mode, words learned,
streak days, accuracy bonuses).

**Reminders.** Configurable reminder time and days with 20+ timezone support and motivational
messages that include the user's progress.

**Learning statistics.** Per-level and overall progress bars, quiz history, word breakdown
(learned / in progress / difficult), streak tracking, and achievements.

**Admin analytics panel.** Dashboard with cohort analysis, churn detection, CSV export,
localized broadcast messaging, and per-user detailed statistics.

---

## Architecture

A clean, layered async architecture (~12k lines of Python):

```
app/
├── bot/
│   ├── handlers/        # Telegram update handlers (quiz, leaderboard, reminders, admin, start)
│   ├── keyboards/       # Inline keyboard builders
│   ├── states.py        # FSM states
│   └── utils.py
├── services/            # Business logic (quiz engine, SRS, leaderboards) — DB-aware, handler-agnostic
├── database/
│   ├── models.py        # SQLAlchemy 2.0 ORM models (12 tables)
│   ├── enums.py         # CEFR levels, POS, quiz modes, translation modes
│   └── session.py       # Async engine / session factory
├── schedulers/          # APScheduler jobs (reminders, monthly season rollover)
├── locales/             # ru / uk / en / tr translation dictionaries
├── core/                # Logging, Sentry integration
├── config.py            # Pydantic settings (env-driven, no secrets in code)
└── main.py              # Composition root / bot bootstrap

alembic/                 # Versioned database migrations
```

**Design highlights:**

- **Handlers stay thin** — all learning logic (word selection, SRS scoring, distractor generation,
  progress tracking) lives in `services/` and is independently testable.
- **Fully async** end-to-end: `aiogram 3.x` + `SQLAlchemy 2.0` async ORM + `asyncpg`.
- **Schema-versioned** with Alembic; migrations apply automatically on container startup.
- **Config via environment only** — Pydantic `BaseSettings`, no secrets committed to the repo.
- **Observability** — structured logging and optional Sentry error tracking.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Telegram framework | aiogram 3.15 (async) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Scheduling | APScheduler |
| Config | Pydantic Settings |
| Error tracking | Sentry (optional) |
| Deployment | Docker / Docker Compose |

---

## Getting Started

```bash
git clone https://github.com/Kanaki-K/GenauLingua.git
cd GenauLingua

cp .env.example .env      # fill in BOT_TOKEN, ADMIN_USER, DB credentials
docker compose up -d --build
```

Database migrations run automatically on container startup. See
[`app/scripts/README.md`](app/scripts/README.md) for rebuilding the word database from an
Excel dataset.

### Configuration

All secrets (bot token, database credentials, admin ID) are supplied via environment variables
in `.env`. **No secrets are stored in the repository.** See [`.env.example`](.env.example) for
the full list of variables.

---

## What This Project Demonstrates

For anyone evaluating this as a portfolio piece, GenauLingua shows end-to-end delivery of:

- **Async Python backend engineering** — non-trivial `aiogram 3` bot with FSM flows, inline
  keyboards, and clean handler/service separation.
- **Relational data modeling** — 12-table PostgreSQL schema with a real migration history.
- **Algorithm design** — a working spaced-repetition engine and weighted word/distractor selection.
- **Product systems** — gamification (seasons, streaks, leaderboards), scheduled jobs, and reminders.
- **Internationalization** — a 4-language product with fully localized content and UI.
- **Data engineering** — an ingestion pipeline that builds a 12k-word multilingual dataset from Excel.
- **DevOps** — containerized, environment-driven deployment running in production.

---

## Privacy

The bot processes only the minimal data needed to run (Telegram ID, learning progress,
preferences). Full details: [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

---

## License

Built as an independent product. The bot is free to use and runs without ads.
