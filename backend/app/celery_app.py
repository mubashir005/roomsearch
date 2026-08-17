"""Celery application + Celery Beat schedule (task section 7)."""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "roomsearch",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Berlin",
    enable_utc=True,
    task_track_started=True,
)

celery_app.conf.beat_schedule = {
    "hourly-search": {
        "task": "app.tasks.run_scheduled_search",
        "schedule": settings.SEARCH_INTERVAL_MINUTES * 60.0,
    },
    "hourly-digest-check": {
        "task": "app.tasks.run_hourly_digest",
        "schedule": crontab(minute=5),
    },
    "daily-digest-check": {
        "task": "app.tasks.run_daily_digest",
        "schedule": crontab(hour=8, minute=0),
    },
}
