import asyncio
from datetime import datetime

from app.config import get_settings
from app.models import (
    AnmeldungStatus,
    FurnishedStatus,
    Listing,
    ListingStatus,
    NotificationLog,
    RentalType,
)
from app.notifications import formatting
from app.notifications.dispatcher import dispatch_notifications
from app.notifications.email_notifier import send_email
from app.notifications.telegram_notifier import send_telegram


def make_listing(db_session, **overrides) -> Listing:
    base = dict(
        canonical_url="https://example.invalid/1",
        content_hash="hash1",
        title="1-Zimmer-Wohnung in Hannover-List",
        district="List",
        city="Hannover",
        rent_warm=480,
        rent_warm_is_estimated=False,
        size_sqm=32,
        rooms=1,
        furnished=FurnishedStatus.FURNISHED,
        private_bathroom=True,
        private_kitchen=True,
        anmeldung=AnmeldungStatus.POSSIBLE,
        availability_date=datetime(2026, 10, 1),
        rental_type=RentalType.LONG_TERM,
        match_score=94,
        match_explanation=["✓ Warm rent €480 <= €500", "✓ Hannover core district (List)"],
        status=ListingStatus.MATCHED,
    )
    base.update(overrides)
    listing = Listing(**base)
    db_session.add(listing)
    db_session.commit()
    db_session.refresh(listing)
    return listing


def test_email_subject_single_listing(db_session):
    listing = make_listing(db_session)
    subject = formatting.email_subject([listing])
    assert "480" in subject or "€480" in subject
    assert "List" in subject


def test_email_subject_multiple_listings(db_session):
    l1 = make_listing(db_session)
    l2 = make_listing(db_session, canonical_url="https://example.invalid/2", content_hash="hash2")
    subject = formatting.email_subject([l1, l2])
    assert "2 new listings" in subject


def test_email_body_contains_required_fields(db_session):
    listing = make_listing(db_session)
    text = formatting.email_body_text([listing])
    assert "480" in text
    assert "32" in text
    assert "List" in text
    assert "01.10.2026" in text
    assert "94/100" in text
    assert listing.canonical_url in text


def test_telegram_message_format(db_session):
    listing = make_listing(db_session)
    msg = formatting.telegram_message(listing)
    assert "NEW HANNOVER MATCH" in msg
    assert "480" in msg
    assert "94/100" in msg


def test_send_email_disabled_returns_false_no_network(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    listing = make_listing(db_session)
    ok, error = send_email([listing])
    assert ok is False
    assert "disabled" in error.lower()


def test_send_telegram_disabled_returns_false_no_network(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    listing = make_listing(db_session)
    ok, error = asyncio.run(send_telegram(listing))
    assert ok is False
    assert "disabled" in error.lower()


def test_dispatch_notifications_creates_dashboard_log_and_marks_notified(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")

    listing = make_listing(db_session)
    asyncio.run(dispatch_notifications(db_session, [listing]))

    db_session.refresh(listing)
    assert listing.notified_at is not None
    assert listing.notification_count == 1
    assert listing.status == ListingStatus.NOTIFIED

    logs = db_session.query(NotificationLog).filter(NotificationLog.listing_id == listing.id).all()
    assert any(l.channel == "dashboard" for l in logs)
    get_settings.cache_clear()
