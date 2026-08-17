"""Fan a batch of qualifying listings out to whichever notification channels
are enabled, log the results for the dashboard, and mark listings as
notified so they are never re-notified for the same match.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Listing, ListingStatus, NotificationLog
from app.notifications.email_notifier import send_email
from app.notifications.formatting import email_subject, telegram_message
from app.notifications.telegram_notifier import send_telegram


async def dispatch_notifications(db: Session, listings: list[Listing]) -> None:
    if not listings:
        return
    settings = get_settings()

    # Highest-quality matches first (section 22: "Send high-quality listings first").
    listings = sorted(listings, key=lambda l: l.match_score, reverse=True)

    if settings.EMAIL_NOTIFICATIONS_ENABLED:
        success, error = send_email(listings)
        db.add(
            NotificationLog(
                channel="email",
                subject=email_subject(listings),
                body_preview=f"{len(listings)} listing(s)",
                success=success,
                error=error,
            )
        )

    if settings.TELEGRAM_NOTIFICATIONS_ENABLED:
        for listing in listings:
            success, error = await send_telegram(listing)
            db.add(
                NotificationLog(
                    listing_id=listing.id,
                    channel="telegram",
                    body_preview=telegram_message(listing)[:200],
                    success=success,
                    error=error,
                )
            )

    for listing in listings:
        db.add(
            NotificationLog(
                listing_id=listing.id,
                channel="dashboard",
                subject=listing.title,
                body_preview=f"Match score {listing.match_score}/100",
                success=True,
            )
        )
        listing.notified_at = datetime.utcnow()
        listing.notification_count += 1
        listing.status = ListingStatus.NOTIFIED

    db.commit()
