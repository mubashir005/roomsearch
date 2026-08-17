"""SMTP email notifications. Credentials come from environment variables only
(see .env.example) -- never hardcoded. Works with Gmail, Outlook, or any
generic SMTP server."""
from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings
from app.models import Listing
from app.notifications.formatting import email_body_html, email_body_text, email_subject

logger = logging.getLogger(__name__)


def send_email(listings: list[Listing]) -> tuple[bool, str | None]:
    settings = get_settings()

    if not settings.EMAIL_NOTIFICATIONS_ENABLED:
        return False, "Email notifications disabled."
    if not settings.SMTP_HOST or not settings.NOTIFICATION_EMAIL:
        return False, "SMTP_HOST or NOTIFICATION_EMAIL not configured."
    if not listings:
        return False, "No listings to notify about."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = email_subject(listings)
    msg["From"] = settings.SMTP_USERNAME or settings.NOTIFICATION_EMAIL
    msg["To"] = settings.NOTIFICATION_EMAIL

    msg.attach(MIMEText(email_body_text(listings), "plain", "utf-8"))
    msg.attach(MIMEText(email_body_html(listings), "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [settings.NOTIFICATION_EMAIL], msg.as_string())
        return True, None
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to send email notification")
        return False, str(exc)
