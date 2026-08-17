"""Application configuration, loaded from environment variables / .env."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    SECRET_KEY: str = "change-me-in-production"
    ENVIRONMENT: str = "development"

    # If set, every API request (except /api/health) must include a matching
    # `X-API-Key` header. Leave unset for local/self-hosted use behind your
    # own network; set it whenever the API is reachable from the public
    # internet (see README "Free deployment").
    API_KEY: str = ""

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://roomsearch:roomsearch@localhost:5432/roomsearch"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        # Managed Postgres providers (Neon, Supabase, Render, ...) hand out
        # bare `postgresql://` URLs; SQLAlchemy needs the driver in the
        # scheme to pick psycopg2 explicitly.
        if v.startswith("postgresql://"):
            return "postgresql+psycopg2://" + v[len("postgresql://") :]
        return v

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # Scheduler
    SEARCH_INTERVAL_MINUTES: int = 60

    # Email / SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    NOTIFICATION_EMAIL: str = ""
    EMAIL_NOTIFICATIONS_ENABLED: bool = False

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_NOTIFICATIONS_ENABLED: bool = False

    # Notification mode: immediate | hourly_digest | daily_digest
    NOTIFICATION_MODE: str = "immediate"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
