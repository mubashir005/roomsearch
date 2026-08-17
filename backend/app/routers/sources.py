"""Source admin API (task section 13): status, enable/disable, priority,
config, manual test/run per source."""
from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Source, SourceStatus
from app.schemas import SourceOut, SourceUpdateIn
from app.sources.registry import SOURCE_REGISTRY, instantiate

router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return list(db.execute(select(Source).order_by(Source.priority)).scalars().all())


@router.patch("/{source_key}", response_model=SourceOut)
def update_source(source_key: str, payload: SourceUpdateIn, db: Session = Depends(get_db)):
    source = db.execute(select(Source).where(Source.key == source_key)).scalars().first()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    adapter_cls = SOURCE_REGISTRY.get(source_key)
    if payload.enabled is True and adapter_cls and not adapter_cls.available:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot enable {source_key}: {adapter_cls.unavailable_reason or 'not available'}",
        )

    if payload.enabled is not None:
        source.enabled = payload.enabled
    if payload.priority is not None:
        source.priority = payload.priority
    if payload.config is not None:
        source.config = payload.config
    db.commit()
    db.refresh(source)
    return source


@router.post("/{source_key}/test")
def test_source(source_key: str, db: Session = Depends(get_db)):
    source = db.execute(select(Source).where(Source.key == source_key)).scalars().first()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    adapter = instantiate(source_key, config=source.config)
    if adapter is None:
        raise HTTPException(status_code=404, detail="No adapter registered for this source key")

    start = time.monotonic()
    health = asyncio.run(adapter.health_check())
    elapsed = int((time.monotonic() - start) * 1000)

    source.status = SourceStatus(health.status)
    source.last_response_time_ms = health.response_time_ms or elapsed
    if health.ok:
        source.last_success_at = __import__("datetime").datetime.utcnow()
        source.last_error = None
    else:
        source.last_error = health.message
        source.last_error_at = __import__("datetime").datetime.utcnow()
    db.commit()

    return {"ok": health.ok, "status": health.status, "message": health.message, "response_time_ms": elapsed}


@router.post("/{source_key}/run")
def run_source_now(source_key: str, db: Session = Depends(get_db)):
    source = db.execute(select(Source).where(Source.key == source_key)).scalars().first()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    from app.pipeline import get_active_profiles

    adapter = instantiate(source_key, config=source.config)
    if adapter is None:
        raise HTTPException(status_code=404, detail="No adapter registered for this source key")

    profiles = get_active_profiles(db)
    primary_profile = profiles[0] if profiles else None
    result = asyncio.run(adapter.search(primary_profile))

    from app.pipeline import best_score, upsert_listing  # reuse scoring/dedup logic

    new_count = matches_count = 0
    for normalized in result.listings:
        listing, is_new, is_updated, is_merge = upsert_listing(db, normalized)
        best = best_score(listing, profiles) if profiles else None
        if best:
            profile, score_result = best
            listing.match_score = score_result.score
            listing.match_explanation = [f"✓ {r}" for r in score_result.reasons] + [
                f"✗ {w}" for w in score_result.warnings
            ]
            if score_result.score >= profile.min_score_to_notify:
                matches_count += 1
        if is_new:
            new_count += 1

    source.last_listings_found = result.found_count
    source.last_matching_found = matches_count
    source.status = SourceStatus.OK if not result.errors else (SourceStatus.LIMITED if result.listings else SourceStatus.ERROR)
    if result.errors:
        source.last_error = "; ".join(result.errors)
    db.commit()

    return {
        "found": result.found_count,
        "parsed": result.parsed_count,
        "new": new_count,
        "matches": matches_count,
        "errors": result.errors,
    }
