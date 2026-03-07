# GenauLingua

GenauLingua is a Telegram bot designed for structured and long-term German vocabulary learning.

The project focuses on adaptive learning through spaced repetition (SRS), detailed user statistics, competitive leaderboards, and flexible learning configuration.

## Project Status

- Supported levels: **A1–B1**
- Levels B2–C2 — in development
- Vocabulary database: **~3,000 words**
- Interface languages: **Russian, Ukrainian, English, Turkish**
- Telegram-based application
- Docker-ready deployment

## Features

### Adaptive Learning (SRS)
- Individual repetition intervals per word
- Priority for weak or frequently mistaken words
- Reduced frequency for well-mastered vocabulary
- Performance-based difficulty adjustment

### Multi-Language Support
- 4 interface languages: RU, UK, EN, TR
- 4 translation modes: DE↔RU, DE↔UA, DE↔EN, DE↔TR
- Reverse mode (e.g. RU→DE) for advanced learners
- Full localization of all UI elements

### Rating & Leaderboard
- Monthly rating system with point-based scoring
- All-time (lifetime) rating with cumulative points
- Top-10 leaderboard table
- Automatic season management (monthly reset + awards)
- Win streaks and achievement titles
- Scoring: quizzes (+10), reverse (+5), words learned (+2), streak days (+3), accuracy bonuses

### Notifications & Reminders
- Customizable reminder time and days
- Timezone support (20+ cities)
- Motivational messages with progress stats
- Streak tracking and encouragement

### User Statistics
- Progress bar per level and overall
- Detailed quiz history with results
- Words learned / in progress / difficult breakdown
- Streak tracking (daily activity)
- Achievement system based on progress

### Quiz System
- 25-word quiz sessions
- 4-option multiple choice
- Instant feedback with correct answer and examples
- Error repetition mode after quiz completion
- Smart distractor selection (same POS, different article)

### Administration
- Admin panel with analytics dashboard
- Cohort analysis and churn detection
- CSV export (users, quizzes)
- Localized broadcast messaging to all users
- Per-user detailed statistics

## Technology Stack

- **Python 3.11**
- **aiogram 3.15** (Telegram Bot API)
- **PostgreSQL 16**
- **SQLAlchemy 2.0** (async ORM)
- **Alembic** (database migrations)
- **APScheduler** (reminders + season management)
- **Docker / Docker Compose**

## Getting Started (Docker)

Clone the repository:

```bash
git clone https://github.com/lodk666/GenauLingua.git
cd GenauLingua
```

Start the containers:

```bash
docker compose up -d --build
```

## Database Migrations

Apply migrations:

```bash
docker compose exec app alembic upgrade head
```

Create a new migration:

```bash
alembic revision --autogenerate -m "description"
```

## Diagnostics

Run full system check:

```bash
python app/scripts/check_full_system.py
```

Run leaderboard data integrity check:

```bash
python app/scripts/check_leaderboard.py
```

## Broadcast Updates

Send localized update to all users:

```bash
python app/scripts/broadcast_update.py --dry-run   # preview
python app/scripts/broadcast_update.py --test <id>  # test single user
python app/scripts/broadcast_update.py              # send to all
```

## Logs

View application logs:

```bash
docker compose logs -f app
```

## Configuration

All sensitive data (bot tokens, database credentials, admin IDs) are provided via environment variables.

Secrets are not stored in the repository.

## Privacy

Privacy policy is available in [PRIVACY_POLICY.md](PRIVACY_POLICY.md).

## Roadmap

- Add support for B2–C2 levels
- Expand vocabulary database to 30,000 words
- Word categories (food, transport, work, travel)
- Achievement badges system
- New learning modes beyond quizzes
- Structured logging and monitoring
- Production-grade observability and stability improvements