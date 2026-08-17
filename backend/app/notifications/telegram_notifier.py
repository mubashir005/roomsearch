"""Telegram Bot notifications."""
from __future__ import annotations

import logging

import httpx

from app.config import get_settings
from app.models import Listing
from app.notifications.formatting import telegram_message

logger = logging.getLogger(__name__)


async def send_telegram(listing: Listing) -> tuple[bool, str | None]:
    settings = get_settings()

    if not settings.TELEGRAM_NOTIFICATIONS_ENABLED:
        return False, "Telegram notifications disabled."
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return False, "TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured."

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": telegram_message(listing),
        "disable_web_page_preview": False,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        return True, None
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to send Telegram notification")
        return False, str(exc)
