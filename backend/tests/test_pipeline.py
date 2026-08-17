"""Integration test for the full search pipeline: search -> normalize ->
score -> dedupe -> persist -> notify, using the mock/demo source so no
external network access is required."""
import asyncio

from app.config import get_settings
from app.models import ListingStatus, NotificationLog, SearchProfile, Source
from app.pipeline import run_search


def seed_minimal(db_session):
    db_session.add(
        Source(key="mock_demo", name="Mock/Demo Source", enabled=True, priority=100, config={})
    )
    db_session.add(
        SearchProfile(
            name="Test Profile",
            active=True,
            city="Hannover",
            max_rent_warm=500,
            preferred_size_min=20,
            preferred_size_max=50,
            min_score_to_notify=50,
        )
    )
    db_session.commit()


def test_run_search_discovers_and_scores_listings(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("NOTIFICATION_MODE", "immediate")
    seed_minimal(db_session)

    run = asyncio.run(run_search(db_session, trigger="manual"))

    assert run.total_discovered == 4
    assert run.total_new == 4
    # 3 of the 4 mock fixtures are within Hannover budget/size; the Garbsen
    # 2-room over-budget listing should not qualify.
    assert run.total_matching >= 1
    assert run.total_matching < 4
    get_settings.cache_clear()


def test_run_search_notifies_only_once_per_listing(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("NOTIFICATION_MODE", "immediate")
    seed_minimal(db_session)

    asyncio.run(run_search(db_session, trigger="manual"))
    first_run_notifications = db_session.query(NotificationLog).filter(
        NotificationLog.channel == "dashboard"
    ).count()
    assert first_run_notifications >= 1

    # Second run sees the exact same fixtures again -- nothing new, nothing
    # should be re-notified (task section 22: don't spam for the same listing).
    run2 = asyncio.run(run_search(db_session, trigger="manual"))
    assert run2.total_new == 0

    second_run_notifications = db_session.query(NotificationLog).filter(
        NotificationLog.channel == "dashboard"
    ).count()
    assert second_run_notifications == first_run_notifications
    get_settings.cache_clear()


def test_run_search_marks_matched_listings_notified_status(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("NOTIFICATION_MODE", "immediate")
    seed_minimal(db_session)

    asyncio.run(run_search(db_session, trigger="manual"))

    from app.models import Listing

    notified = db_session.query(Listing).filter(Listing.status == ListingStatus.NOTIFIED).all()
    assert len(notified) >= 1
    for listing in notified:
        assert listing.match_score >= 50
        assert listing.notified_at is not None
    get_settings.cache_clear()


def test_digest_mode_defers_notification_until_digest_sent(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("NOTIFICATION_MODE", "hourly_digest")
    seed_minimal(db_session)

    asyncio.run(run_search(db_session, trigger="manual"))

    from app.models import Listing

    matched_not_notified = db_session.query(Listing).filter(
        Listing.status == ListingStatus.MATCHED, Listing.notified_at.is_(None)
    ).all()
    assert len(matched_not_notified) >= 1

    from app.notifications.digest import send_digest

    sent_count = asyncio.run(send_digest(db_session))
    assert sent_count == len(matched_not_notified)

    still_pending = db_session.query(Listing).filter(
        Listing.status == ListingStatus.MATCHED, Listing.notified_at.is_(None)
    ).count()
    assert still_pending == 0
    get_settings.cache_clear()
