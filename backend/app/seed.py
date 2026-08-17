"""Seed default sources and search profiles. Idempotent -- safe to run on
every startup (task section 25: "Seed data")."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.matching.location import CORE_DISTRICTS, NEARBY_AREAS
from app.models import SearchProfile, Source
from app.sources.registry import SOURCE_REGISTRY

DEFAULT_SOURCE_CONFIG = {
    "mock_demo": {"enabled": True, "priority": 100, "config": {}},
    "rss_generic": {
        "enabled": False,
        "priority": 10,
        "config": {"feed_url": ""},  # set a real feed URL, then enable via API/dashboard
    },
    "meinestadt": {"enabled": False, "priority": 20, "config": {"feed_url": ""}},
    "wg_gesucht": {"enabled": False, "priority": 30, "config": {}},
    "kleinanzeigen": {"enabled": False, "priority": 40, "config": {}},
    "immoscout24": {"enabled": False, "priority": 50, "config": {}},
    "immowelt": {"enabled": False, "priority": 60, "config": {}},
    "immonet": {"enabled": False, "priority": 70, "config": {}},
    "housinganywhere": {"enabled": False, "priority": 80, "config": {}},
    "wunderflats": {"enabled": False, "priority": 90, "config": {}},
}


def seed_sources(db: Session) -> None:
    for key, adapter_cls in SOURCE_REGISTRY.items():
        existing = db.execute(select(Source).where(Source.key == key)).scalars().first()
        if existing is not None:
            continue
        defaults = DEFAULT_SOURCE_CONFIG.get(key, {"enabled": False, "priority": 100, "config": {}})
        db.add(
            Source(
                key=key,
                name=adapter_cls.display_name,
                enabled=defaults["enabled"] and adapter_cls.available,
                priority=defaults["priority"],
                config=defaults["config"],
                unavailable_reason=adapter_cls.unavailable_reason,
            )
        )
    db.commit()


def seed_search_profiles(db: Session) -> None:
    existing = db.execute(select(SearchProfile)).scalars().first()
    if existing is not None:
        return

    db.add(
        SearchProfile(
            name="Hannover Studio October",
            active=True,
            city="Hannover",
            preferred_districts=CORE_DISTRICTS,
            nearby_areas=NEARBY_AREAS,
            max_rent_warm=500,
            min_size_sqm=15,
            preferred_size_min=20,
            preferred_size_max=50,
            max_rooms=1,
            available_from=datetime(2026, 10, 1),
            anmeldung_preference="preferred",
            notification_mode="immediate",
            email_enabled=True,
            telegram_enabled=False,
            min_score_to_notify=50,
            scoring_weights={},
        )
    )
    db.add(
        SearchProfile(
            name="Hannover Ultra Budget",
            active=True,
            city="Hannover",
            preferred_districts=CORE_DISTRICTS,
            nearby_areas=NEARBY_AREAS,
            max_rent_warm=400,
            min_size_sqm=15,
            preferred_size_min=18,
            preferred_size_max=45,
            max_rooms=1,
            available_from=datetime(2026, 10, 1),
            anmeldung_preference="preferred",
            notification_mode="immediate",
            email_enabled=True,
            telegram_enabled=False,
            min_score_to_notify=45,
            scoring_weights={},
        )
    )
    db.commit()


def run_seed(db: Session) -> None:
    seed_sources(db)
    seed_search_profiles(db)


if __name__ == "__main__":
    from app.database import SessionLocal

    session = SessionLocal()
    try:
        run_seed(session)
        print("Seed complete.")
    finally:
        session.close()
