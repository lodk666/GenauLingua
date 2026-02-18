GenauLingua

GenauLingua is a Telegram bot designed for structured and long-term German vocabulary learning.

The project focuses on adaptive learning through spaced repetition (SRS), detailed user statistics, and flexible learning configuration.

Project Status

Supported levels: A1–B1

Levels B2–C2 — in development

Vocabulary database: ~3,000 words

Telegram-based application

Docker-ready deployment

Features
Adaptive Learning (SRS)

Individual repetition intervals per word

Priority for weak or frequently mistaken words

Reduced frequency for well-mastered vocabulary

Performance-based difficulty adjustment

User Statistics

Tracking of correct and incorrect answers

Individual learning progress

Weak-word detection

Personalized learning dynamics

Flexible Configuration

Level selection (A1–B1)

Adaptive word selection logic

Learning behavior customization

Environment-based configuration

Administration

Vocabulary management via Telegram

Add / edit word entries

Access control via ADMIN_IDS

Database-backed word management

Technology Stack

Python

PostgreSQL

SQLAlchemy

Alembic (database migrations)

Docker / Docker Compose

Telegram Bot API

Getting Started (Docker)

Clone the repository:

git clone https://github.com/lodk666/GenauLingua.git
cd GenauLingua


Start the containers:

docker compose up -d --build

Database Migrations

Apply migrations:

docker compose exec app alembic upgrade head


Create a new migration:

alembic revision --autogenerate -m "description"

Logs

View application logs:

docker compose logs -f app

Configuration

All sensitive data (bot tokens, database credentials, admin IDs) are provided via environment variables.

Secrets are not stored in the repository.

Privacy

Privacy policy is available in PRIVACY_POLICY.md.

Roadmap

Add support for B2–C2 levels

Expand vocabulary database

Improve analytics and learning insights

Implement structured logging and monitoring

Production-grade observability and stability improvements