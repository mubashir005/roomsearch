"""Quick Add: manually submit a listing you found yourself (e.g. copied out
of a ChatGPT search, or a page you browsed personally) so it runs through
the same scoring/dedup/notification pipeline as every other source.

This is deliberately NOT an automated fetch of any kind -- the user
supplies the text. That's what keeps it on the right side of the ToS
restrictions documented in app/sources/disabled.py: a person reading a
webpage and pasting what they found is just... using the internet. An
adapter that has code (or an LLM) autonomously browse/scrape those same
sites on a schedule would not be materially different from a scraper and
is exactly what this project does not do.
"""
from __future__ import annotations

import hashlib
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_parsing import parse_listing_with_ai
from app.config import get_settings
from app.database import get_db
from app.dedup.engine import normalize_url
from app.listing_schema import NormalizedListing
from app.matching import german_terms, price_parser
from app.matching.location import extract_district
from app.models import ListingStatus, Source, SourceStatus
from app.pipeline import best_score, get_active_profiles, upsert_listing
from app.schemas import ListingOut, QuickAddIn, QuickAddOut

router = APIRouter(prefix="/api/listings", tags=["quick-add"])

MANUAL_SOURCE_KEY = "manual"


def _ensure_manual_source(db: Session) -> None:
    existing = db.execute(select(Source).where(Source.key == MANUAL_SOURCE_KEY)).scalars().first()
    if existing is None:
        db.add(
            Source(
                key=MANUAL_SOURCE_KEY,
                name="Quick Add (manual)",
                enabled=True,
                priority=0,
                config={},
                status=SourceStatus.OK,
                unavailable_reason=None,
            )
        )
        db.commit()


def _parse_ai_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value[:10])
    except ValueError:
        return None


@router.post("/quick-add", response_model=QuickAddOut)
async def quick_add_listing(payload: QuickAddIn, db: Session = Depends(get_db)):
    _ensure_manual_source(db)
    settings = get_settings()
    text = payload.text.strip()

    # 1. Deterministic parsing first (task section 29).
    rent = price_parser.parse_rent(text)
    fields = {
        "title": text.splitlines()[0][:200] if text else "Untitled listing",
        "address": None,
        "district": extract_district(text),
        "city": "Hannover",
        "postcode": None,
        "rent_cold": rent.cold,
        "rent_warm": rent.warm,
        "rent_warm_is_estimated": rent.warm_is_estimated,
        "utilities": rent.utilities,
        "heating_cost": rent.heating,
        "size_sqm": german_terms.extract_size_sqm(text),
        "rooms": german_terms.extract_rooms(text),
        "furnished": german_terms.extract_furnished(text),
        "private_bathroom": german_terms.extract_private_bathroom(text),
        "private_kitchen": german_terms.extract_private_kitchen(text),
        "balcony": german_terms.extract_balcony(text),
        "anmeldung": german_terms.extract_anmeldung(text),
        "rental_type": german_terms.extract_rental_type(text),
        "availability_date": None,
    }

    # 2. AI fallback fills ONLY the gaps deterministic parsing left unknown
    # -- it never overrides a value already found (task section 29: "AI
    # parsing should only be used as a fallback").
    used_ai_fallback = False
    ai_fields_filled: list[str] = []
    if settings.OPENAI_API_KEY:
        ai_result = await parse_listing_with_ai(text)
        if ai_result:
            used_ai_fallback = True
            for key, value in ai_result.items():
                if value is None:
                    continue
                current = fields.get(key)
                is_unknown = current is None or current in ("unknown", "")
                if key in fields and is_unknown:
                    fields[key] = value
                    ai_fields_filled.append(key)

    url = payload.url.strip() if payload.url else None
    if url:
        source_listing_id = normalize_url(url)
    else:
        source_listing_id = "text-" + hashlib.sha256(text.lower().encode("utf-8")).hexdigest()[:16]

    normalized = NormalizedListing(
        source_key=MANUAL_SOURCE_KEY,
        source_listing_id=source_listing_id,
        url=url or f"internal://quick-add/{source_listing_id}",
        title=fields["title"] or "Untitled listing",
        description=text,
        address=fields["address"],
        district=fields["district"],
        city=fields["city"] or "Hannover",
        postcode=fields["postcode"],
        rent_cold=fields["rent_cold"],
        rent_warm=fields["rent_warm"],
        rent_warm_is_estimated=bool(fields["rent_warm_is_estimated"]),
        utilities=fields["utilities"],
        heating_cost=fields["heating_cost"],
        size_sqm=fields["size_sqm"],
        rooms=fields["rooms"],
        furnished=fields["furnished"] or "unknown",
        private_bathroom=fields["private_bathroom"],
        private_kitchen=fields["private_kitchen"],
        balcony=fields["balcony"],
        anmeldung=fields["anmeldung"] or "unknown",
        availability_date=_parse_ai_date(fields["availability_date"]),
        rental_type=fields["rental_type"] or "unknown",
        contact_url=url,
        raw_data={"quick_add": True, "used_ai_fallback": used_ai_fallback},
    )

    listing, is_new, is_updated, _is_merge = upsert_listing(db, normalized)

    profiles = get_active_profiles(db)
    best = best_score(listing, profiles) if profiles else None
    qualifies = False
    if best:
        profile, score_result = best
        listing.match_score = score_result.score
        listing.match_explanation = [f"✓ {r}" for r in score_result.reasons] + [
            f"✗ {w}" for w in score_result.warnings
        ]
        qualifies = score_result.score >= profile.min_score_to_notify
        if qualifies and listing.status in (ListingStatus.NEW, ListingStatus.UPDATED):
            listing.status = ListingStatus.MATCHED

    db.commit()
    db.refresh(listing)

    if qualifies and (is_new or is_updated) and listing.notified_at is None and settings.NOTIFICATION_MODE == "immediate":
        from app.notifications.dispatcher import dispatch_notifications

        await dispatch_notifications(db, [listing])
        db.refresh(listing)

    return QuickAddOut(
        listing=ListingOut.model_validate(listing),
        is_new=is_new,
        used_ai_fallback=used_ai_fallback,
        ai_fields_filled=ai_fields_filled,
    )
