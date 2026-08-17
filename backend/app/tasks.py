"""Celery tasks: the hourly search run and digest dispatch."""
from __future__ import annotations

import asyncio
import logging

from app.celery_app import celery_app
from app.config import get_settings
from app.database import SessionLocal
from app.notifications.digest import send_digest
from app.pipeline import run_search

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.run_scheduled_search")
def run_scheduled_search() -> dict:
    db = SessionLocal()
    try:
        run = asyncio.run(run_search(db, trigger="scheduled"))
        return {"run_id": run.id, "new": run.total_new, "matching": run.total_matching}
    except Exception:
        logger.exception("Scheduled search run failed")
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.run_manual_search")
def run_manual_search() -> dict:
    db = SessionLocal()
    try:
        run = asyncio.run(run_search(db, trigger="manual"))
        return {"run_id": run.id, "new": run.total_new, "matching": run.total_matching}
    finally:
        db.close()


@celery_app.task(name="app.tasks.run_hourly_digest")
def run_hourly_digest() -> dict:
    settings = get_settings()
    if settings.NOTIFICATION_MODE != "hourly_digest":
        return {"skipped": True}
    db = SessionLocal()
    try:
        count = asyncio.run(send_digest(db))
        return {"sent": count}
    finally:
        db.close()


@celery_app.task(name="app.tasks.run_daily_digest")
def run_daily_digest() -> dict:
    settings = get_settings()
    if settings.NOTIFICATION_MODE != "daily_digest":
        return {"skipped": True}
    db = SessionLocal()
    try:
        count = asyncio.run(send_digest(db))
        return {"sent": count}
    finally:
        db.close()
