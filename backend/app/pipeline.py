"""Orchestrates one full search run: query every enabled source, normalize,
score, deduplicate, persist, and notify. Used by both the Celery Beat
schedule and the manual "Search Now" API endpoint (task sections 6, 7, 14).
"""
from __future__ import annotations

import time
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dedup.engine import content_hash, find_duplicate, find_existing_by_source_id, normalize_url
from app.listing_schema import NormalizedListing
from app.matching.scoring import score_listing
from app.models import Listing, ListingSourceRecord, ListingStatus, SearchProfile, SearchRun, Source, SourceStatus
from app.sources.registry import instantiate

_MERGEABLE_FIELDS = [
    "title", "description", "address", "district", "postcode", "rent_cold", "rent_warm",
    "rent_warm_is_estimated", "utilities", "heating_cost", "deposit", "size_sqm", "rooms",
    "bathrooms", "floor", "furnished", "kitchen", "private_kitchen", "private_bathroom",
    "balcony", "anmeldung", "availability_date", "rental_type", "images",
]


def get_active_profiles(db: Session) -> list[SearchProfile]:
    return list(db.execute(select(SearchProfile).where(SearchProfile.active.is_(True))).scalars().all())


def best_score(listing: Listing, profiles: list[SearchProfile]):
    best = None
    for profile in profiles:
        result = score_listing(
            listing,
            max_rent_warm=profile.max_rent_warm,
            preferred_size_min=profile.preferred_size_min,
            preferred_size_max=profile.preferred_size_max,
            weights=profile.scoring_weights,
        )
        if best is None or result.score > best[1].score:
            best = (profile, result)
    return best


def _get_or_create_source_record(db: Session, listing: Listing, normalized: NormalizedListing) -> ListingSourceRecord:
    record = db.execute(
        select(ListingSourceRecord).where(
            ListingSourceRecord.source_key == normalized.source_key,
            ListingSourceRecord.source_listing_id == normalized.source_listing_id,
        )
    ).scalars().first()

    if record is None:
        record = ListingSourceRecord(
            listing_id=listing.id,
            source_key=normalized.source_key,
            source_listing_id=normalized.source_listing_id,
            url=normalized.url,
            raw_data=normalized.raw_data,
        )
        db.add(record)
    else:
        record.last_seen_at = datetime.utcnow()
        record.raw_data = normalized.raw_data
        record.listing_id = listing.id
    return record


def upsert_listing(db: Session, normalized: NormalizedListing) -> tuple[Listing, bool, bool, bool]:
    """Create or update the canonical Listing for a normalized source
    sighting. Returns (listing, is_new_canonical, is_updated, is_cross_source_merge)."""
    existing = find_existing_by_source_id(db, normalized.source_key, normalized.source_listing_id)
    is_cross_source_merge = False

    if existing is None:
        existing = find_duplicate(db, normalized)
        if existing is not None:
            is_cross_source_merge = True

    chash = content_hash(normalized)
    is_new = False
    is_updated = False

    if existing is None:
        listing = Listing(
            canonical_url=normalize_url(normalized.url),
            content_hash=chash,
            title=normalized.title,
            description=normalized.description,
            address=normalized.address,
            district=normalized.district,
            city=normalized.city,
            postcode=normalized.postcode,
            latitude=normalized.latitude,
            longitude=normalized.longitude,
            rent_cold=normalized.rent_cold,
            rent_warm=normalized.rent_warm,
            rent_warm_is_estimated=normalized.rent_warm_is_estimated,
            utilities=normalized.utilities,
            heating_cost=normalized.heating_cost,
            deposit=normalized.deposit,
            size_sqm=normalized.size_sqm,
            rooms=normalized.rooms,
            bathrooms=normalized.bathrooms,
            floor=normalized.floor,
            furnished=normalized.furnished,
            kitchen=normalized.kitchen,
            private_kitchen=normalized.private_kitchen,
            private_bathroom=normalized.private_bathroom,
            balcony=normalized.balcony,
            anmeldung=normalized.anmeldung,
            availability_date=normalized.availability_date,
            rental_type=normalized.rental_type,
            contact_name=normalized.contact_name,
            contact_company=normalized.contact_company,
            contact_url=normalized.contact_url,
            images=normalized.images,
            status=ListingStatus.NEW,
            raw_data=normalized.raw_data,
        )
        db.add(listing)
        db.flush()
        is_new = True
    else:
        listing = existing
        if listing.content_hash != chash:
            is_updated = True
            listing.last_changed_at = datetime.utcnow()
            for field_name in _MERGEABLE_FIELDS:
                value = getattr(normalized, field_name)
                if value not in (None, "", [], "unknown"):
                    setattr(listing, field_name, value)
            listing.content_hash = chash
            if listing.status in (ListingStatus.EXPIRED, ListingStatus.REMOVED):
                listing.status = ListingStatus.UPDATED

    listing.last_seen_at = datetime.utcnow()
    _get_or_create_source_record(db, listing, normalized)

    return listing, is_new, is_updated, is_cross_source_merge


async def run_search(db: Session, trigger: str = "scheduled") -> SearchRun:
    settings = get_settings()
    run = SearchRun(trigger=trigger, source_results=[], errors=[])
    db.add(run)
    db.flush()

    profiles = get_active_profiles(db)
    primary_profile = profiles[0] if profiles else None

    sources = list(
        db.execute(select(Source).where(Source.enabled.is_(True)).order_by(Source.priority)).scalars().all()
    )

    total_discovered = total_parsed = total_matching = total_new = total_duplicates = 0
    source_results_log: list[dict] = []
    new_matches_for_notification: list[Listing] = []

    for source_row in sources:
        adapter = instantiate(source_row.key, config=source_row.config)
        if adapter is None:
            continue

        start = time.monotonic()
        try:
            search_result = await adapter.search(primary_profile)
        except Exception as exc:  # noqa: BLE001 - one source failing must not stop the rest (section 21)
            source_row.status = SourceStatus.ERROR
            source_row.last_error = str(exc)
            source_row.last_error_at = datetime.utcnow()
            run.errors.append({"source": source_row.key, "error": str(exc)})
            source_results_log.append(
                {"source": source_row.key, "found": 0, "parsed": 0, "matches": 0, "new": 0, "error": str(exc)}
            )
            continue
        elapsed_ms = int((time.monotonic() - start) * 1000)

        if search_result.errors and not search_result.listings:
            source_row.status = SourceStatus.ERROR
            source_row.last_error = "; ".join(search_result.errors)
            source_row.last_error_at = datetime.utcnow()
            run.errors.append({"source": source_row.key, "error": source_row.last_error})
        elif search_result.errors:
            source_row.status = SourceStatus.LIMITED
            source_row.last_error = "; ".join(search_result.errors)
            source_row.last_error_at = datetime.utcnow()
        else:
            source_row.status = SourceStatus.OK
            source_row.last_success_at = datetime.utcnow()
            source_row.last_error = None

        source_row.last_response_time_ms = search_result.response_time_ms or elapsed_ms
        source_row.last_listings_found = search_result.found_count

        source_new = source_matches = source_duplicates = 0

        for normalized in search_result.listings:
            listing, is_new, is_updated, is_merge = upsert_listing(db, normalized)

            best = best_score(listing, profiles) if profiles else None
            qualifies = False
            if best:
                profile, score_result = best
                listing.match_score = score_result.score
                listing.match_explanation = [f"✓ {r}" for r in score_result.reasons] + [
                    f"✗ {w}" for w in score_result.warnings
                ]
                qualifies = score_result.score >= profile.min_score_to_notify

            if qualifies:
                source_matches += 1
                if listing.status in (ListingStatus.NEW, ListingStatus.UPDATED):
                    listing.status = ListingStatus.MATCHED

            if is_new:
                source_new += 1
                total_new += 1
                if qualifies:
                    new_matches_for_notification.append(listing)
            elif is_updated and qualifies and listing.notified_at is None:
                new_matches_for_notification.append(listing)

            if is_merge:
                source_duplicates += 1

        source_row.last_matching_found = source_matches
        total_discovered += search_result.found_count
        total_parsed += search_result.parsed_count
        total_matching += source_matches
        total_duplicates += source_duplicates

        source_results_log.append(
            {
                "source": source_row.key,
                "found": search_result.found_count,
                "parsed": search_result.parsed_count,
                "matches": source_matches,
                "new": source_new,
                "duplicates_merged": source_duplicates,
                "response_time_ms": source_row.last_response_time_ms,
            }
        )

    run.total_discovered = total_discovered
    run.total_parsed = total_parsed
    run.total_matching = total_matching
    run.total_new = total_new
    run.total_duplicates_merged = total_duplicates
    run.source_results = source_results_log
    run.finished_at = datetime.utcnow()
    db.commit()

    # Dedupe notification list (a listing could be appended once per matching
    # source sighting within the same run) and only auto-send in immediate mode.
    unique_matches = list({l.id: l for l in new_matches_for_notification}.values())
    if unique_matches and settings.NOTIFICATION_MODE == "immediate":
        from app.notifications.dispatcher import dispatch_notifications

        await dispatch_notifications(db, unique_matches)

    return run
