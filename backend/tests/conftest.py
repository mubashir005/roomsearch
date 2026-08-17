"""Test configuration. Uses a local SQLite file as a stand-in for Postgres so
the test suite has no external dependencies (task section 26: "mock listing
data so tests do not depend on external websites" -- extended here to mean
no external services at all)."""
from __future__ import annotations

import os

TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_roomsearch.db")
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["EMAIL_NOTIFICATIONS_ENABLED"] = "false"
os.environ["TELEGRAM_NOTIFICATIONS_ENABLED"] = "false"
os.environ["NOTIFICATION_MODE"] = "immediate"

import pytest  # noqa: E402

from app.config import get_settings  # noqa: E402

get_settings.cache_clear()

from app import models  # noqa: E402,F401
from app.database import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            pass


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        session.close()
