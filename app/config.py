from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str
    ADMIN_USER: int

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Optional / infra (можно хранить в .env, но боту не обязательно)
    ENV: Optional[str] = None
    LOG_LEVEL: Optional[str] = None
    LOG_DIR: Optional[str] = None
    SENTRY_DSN: Optional[str] = None

    # Docker / Postgres service vars (если лежат в .env — не должны ломать Settings)
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # <-- ключевое: игнорим лишние переменные в .env
    )


settings = Settings()
