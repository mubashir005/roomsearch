"""Dashboard notification feed + unread counter (task section 8C)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NotificationLog
from app.schemas import NotificationLogOut

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationLogOut])
def list_notifications(db: Session = Depends(get_db), limit: int = 50, unread_only: bool = False):
    stmt = select(NotificationLog).order_by(NotificationLog.created_at.desc()).limit(limit)
    if unread_only:
        stmt = select(NotificationLog).where(NotificationLog.read.is_(False)).order_by(
            NotificationLog.created_at.desc()
        ).limit(limit)
    return list(db.execute(stmt).scalars().all())


@router.get("/unread-count")
def unread_count(db: Session = Depends(get_db)):
    count = db.execute(
        select(func.count()).select_from(NotificationLog).where(NotificationLog.read.is_(False))
    ).scalar_one()
    return {"unread": count}


@router.post("/{notification_id}/read")
def mark_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.get(NotificationLog, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.read = True
    db.commit()
    return {"ok": True}


@router.post("/mark-all-read")
def mark_all_read(db: Session = Depends(get_db)):
    db.execute(NotificationLog.__table__.update().values(read=True).where(NotificationLog.read.is_(False)))
    db.commit()
    return {"ok": True}
