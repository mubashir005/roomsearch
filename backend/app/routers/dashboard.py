"""Dashboard summary stats (task section 10)."""
from __future__ import annotations

from datetime import datetime, time as dtime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Listing, Source
from app.schemas import DashboardStatsOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsOut)
def get_stats(db: Session = Depends(get_db)):
    today_start = datetime.combine(datetime.utcnow().date(), dtime.min)

    def count(stmt):
        return db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    new_today = count(select(Listing.id).where(Listing.first_seen_at >= today_start))
    high_priority = count(select(Listing.id).where(Listing.match_score >= 80))
    under_400 = count(select(Listing.id).where(Listing.rent_warm.is_not(None), Listing.rent_warm <= 400))
    between_400_500 = count(
        select(Listing.id).where(Listing.rent_warm.is_not(None), Listing.rent_warm > 400, Listing.rent_warm <= 500)
    )
    anmeldung_confirmed = count(select(Listing.id).where(Listing.anmeldung == "possible"))
    furnished = count(select(Listing.id).where(Listing.furnished == "furnished"))
    unseen = count(select(Listing.id).where(Listing.notified_at.is_(None)))

    sources_total = count(select(Source.id))
    sources_online = count(select(Source.id).where(Source.status == "ok"))

    return DashboardStatsOut(
        new_today=new_today,
        high_priority=high_priority,
        under_400=under_400,
        between_400_and_500=between_400_500,
        anmeldung_confirmed=anmeldung_confirmed,
        furnished=furnished,
        unseen=unseen,
        sources_online=sources_online,
        sources_total=sources_total,
    )
