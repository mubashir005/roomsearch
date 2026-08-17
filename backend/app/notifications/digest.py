"""Digest-mode notification sending: batches all matched-but-not-yet-notified
listings into a single email/Telegram send (task section 9)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Listing, ListingStatus


async def send_digest(db: Session) -> int:
    stmt = select(Listing).where(Listing.status == ListingStatus.MATCHED, Listing.notified_at.is_(None))
    pending = list(db.execute(stmt).scalars().all())
    if pending:
        from app.notifications.dispatcher import dispatch_notifications

        await dispatch_notifications(db, pending)
    return len(pending)
