"""Listings API: browsing, filtering (task section 11), and export (section 24)."""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Listing
from app.schemas import ListingListOut, ListingOut

router = APIRouter(prefix="/api/listings", tags=["listings"])


def _apply_filters(
    stmt,
    price_min: float | None,
    price_max: float | None,
    rent_type: str | None,
    size_min: float | None,
    size_max: float | None,
    district: str | None,
    available_from: datetime | None,
    furnished: str | None,
    anmeldung: str | None,
    kitchen: bool | None,
    bathroom: bool | None,
    balcony: bool | None,
    long_term: bool | None,
    source: str | None,
    match_score_min: int | None,
    only_new: bool,
    only_unseen: bool,
):
    if price_min is not None:
        stmt = stmt.where(Listing.rent_warm.is_not(None), Listing.rent_warm >= price_min)
    if price_max is not None:
        stmt = stmt.where(Listing.rent_warm.is_not(None), Listing.rent_warm <= price_max)
    if rent_type == "warmmiete":
        stmt = stmt.where(Listing.rent_warm.is_not(None), Listing.rent_warm_is_estimated.is_(False))
    elif rent_type == "kaltmiete":
        stmt = stmt.where(Listing.rent_warm.is_(None), Listing.rent_cold.is_not(None))
    elif rent_type == "unknown":
        stmt = stmt.where(Listing.rent_warm.is_(None), Listing.rent_cold.is_(None))
    if size_min is not None:
        stmt = stmt.where(Listing.size_sqm.is_not(None), Listing.size_sqm >= size_min)
    if size_max is not None:
        stmt = stmt.where(Listing.size_sqm.is_not(None), Listing.size_sqm <= size_max)
    if district:
        stmt = stmt.where(Listing.district == district)
    if available_from is not None:
        stmt = stmt.where(Listing.availability_date.is_not(None), Listing.availability_date >= available_from)
    if furnished:
        stmt = stmt.where(Listing.furnished == furnished)
    if anmeldung:
        stmt = stmt.where(Listing.anmeldung == anmeldung)
    if kitchen is not None:
        stmt = stmt.where(Listing.private_kitchen == kitchen)
    if bathroom is not None:
        stmt = stmt.where(Listing.private_bathroom == bathroom)
    if balcony is not None:
        stmt = stmt.where(Listing.balcony == balcony)
    if long_term is not None:
        stmt = stmt.where(Listing.rental_type == ("long_term" if long_term else "temporary"))
    if match_score_min is not None:
        stmt = stmt.where(Listing.match_score >= match_score_min)
    if only_new:
        stmt = stmt.where(Listing.status == "NEW")
    if only_unseen:
        stmt = stmt.where(Listing.notified_at.is_(None))
    return stmt


@router.get("", response_model=ListingListOut)
def list_listings(
    db: Session = Depends(get_db),
    price_min: float | None = None,
    price_max: float | None = None,
    rent_type: str | None = Query(None, pattern="^(warmmiete|kaltmiete|unknown)$"),
    size_min: float | None = None,
    size_max: float | None = None,
    district: str | None = None,
    available_from: datetime | None = None,
    furnished: str | None = None,
    anmeldung: str | None = None,
    kitchen: bool | None = None,
    bathroom: bool | None = None,
    balcony: bool | None = None,
    long_term: bool | None = None,
    source: str | None = None,
    match_score_min: int | None = None,
    only_new: bool = False,
    only_unseen: bool = False,
    sort: str = Query("match_score_desc", pattern="^(match_score_desc|newest|price_asc|price_desc)$"),
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    stmt = select(Listing)
    if source:
        from app.models import ListingSourceRecord

        stmt = stmt.join(ListingSourceRecord).where(ListingSourceRecord.source_key == source)

    stmt = _apply_filters(
        stmt, price_min, price_max, rent_type, size_min, size_max, district, available_from,
        furnished, anmeldung, kitchen, bathroom, balcony, long_term, source, match_score_min,
        only_new, only_unseen,
    )

    if sort == "match_score_desc":
        stmt = stmt.order_by(Listing.match_score.desc(), Listing.first_seen_at.desc())
    elif sort == "newest":
        stmt = stmt.order_by(Listing.first_seen_at.desc())
    elif sort == "price_asc":
        stmt = stmt.order_by(Listing.rent_warm.asc().nulls_last())
    elif sort == "price_desc":
        stmt = stmt.order_by(Listing.rent_warm.desc().nulls_last())

    all_items = list(db.execute(stmt).unique().scalars().all())
    total = len(all_items)
    page = all_items[offset : offset + limit]
    return ListingListOut(total=total, items=[ListingOut.model_validate(l) for l in page])


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if listing is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingOut.model_validate(listing)


@router.get("/export/csv")
def export_csv(db: Session = Depends(get_db), only_new: bool = False):
    stmt = select(Listing)
    if only_new:
        stmt = stmt.where(Listing.status == "NEW")
    listings = list(db.execute(stmt).scalars().all())

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id", "title", "district", "city", "rent_warm", "rent_warm_is_estimated", "rent_cold",
            "size_sqm", "rooms", "furnished", "anmeldung", "availability_date", "match_score",
            "status", "sources", "canonical_url",
        ]
    )
    for l in listings:
        writer.writerow(
            [
                l.id, l.title, l.district, l.city, l.rent_warm, l.rent_warm_is_estimated, l.rent_cold,
                l.size_sqm, l.rooms, l.furnished.value, l.anmeldung.value,
                l.availability_date.isoformat() if l.availability_date else "",
                l.match_score, l.status.value, "|".join(l.sources_found_on), l.canonical_url,
            ]
        )
    buffer.seek(0)
    filename = "listings_new.csv" if only_new else "listings.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/json")
def export_json(db: Session = Depends(get_db), only_new: bool = False):
    stmt = select(Listing)
    if only_new:
        stmt = stmt.where(Listing.status == "NEW")
    listings = list(db.execute(stmt).scalars().all())
    payload = [ListingOut.model_validate(l).model_dump(mode="json") for l in listings]
    filename = "listings_new.json" if only_new else "listings.json"
    return StreamingResponse(
        iter([json.dumps(payload, indent=2)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
