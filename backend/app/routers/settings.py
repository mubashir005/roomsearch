"""Settings API. Secrets (SMTP/Telegram credentials) are configured via .env
only and are never exposed here -- this endpoint reports effective,
non-secret configuration plus the default scoring weights so the dashboard
can display/explain them (task sections 4, 19)."""
from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.matching.scoring import DEFAULT_WEIGHTS

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_effective_settings():
    settings = get_settings()
    return {
        "notification_mode": settings.NOTIFICATION_MODE,
        "email_notifications_enabled": settings.EMAIL_NOTIFICATIONS_ENABLED,
        "email_configured": bool(settings.SMTP_HOST and settings.NOTIFICATION_EMAIL),
        "telegram_notifications_enabled": settings.TELEGRAM_NOTIFICATIONS_ENABLED,
        "telegram_configured": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
        "search_interval_minutes": settings.SEARCH_INTERVAL_MINUTES,
        "default_scoring_weights": DEFAULT_WEIGHTS,
        "environment": settings.ENVIRONMENT,
    }
