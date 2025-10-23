from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Admin
    ADMIN_ID: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()