"""Duplicate detection: the same apartment posted on multiple sources must
become ONE canonical Listing record with all source URLs attached.

Two-tier strategy:
1. Exact match on (source_key, source_listing_id) -- this is the same
   sighting seen again (an update), not a new duplicate to resolve.
2. Cross-source fuzzy match using a weighted combination of normalized URL,
   address/postcode, rent, size, room count, title similarity, description
   similarity, and image-URL overlap. Listings scoring above the threshold
   are merged into a single canonical record.
"""
from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.listing_schema import NormalizedListing
from app.models import Listing

DUPLICATE_THRESHOLD = 0.60

# Weights sum to 1.0 across the signals that CAN fire; unavailable signals
# (e.g. missing size) are excluded and the rest re-normalized.
_WEIGHTS = {
    "url": 0.20,
    "address": 0.20,
    "rent": 0.15,
    "size": 0.15,
    "rooms": 0.05,
    "title": 0.15,
    "description": 0.05,
    "images": 0.05,
}


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def content_hash(n: NormalizedListing) -> str:
    """Stable hash of the fields that define a materially distinct listing
    version, used to detect when a re-seen listing has actually changed."""
    parts = [
        n.title or "",
        f"{n.rent_warm:.0f}" if n.rent_warm is not None else "",
        f"{n.rent_cold:.0f}" if n.rent_cold is not None else "",
        f"{n.size_sqm:.0f}" if n.size_sqm is not None else "",
        n.availability_date.isoformat() if n.availability_date else "",
        n.furnished,
        n.anmeldung,
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def _text_similarity(a: str | None, b: str | None) -> float | None:
    a, b = (a or "").strip().lower(), (b or "").strip().lower()
    if not a or not b:
        return None
    return SequenceMatcher(None, a, b).ratio()


def _numeric_close(a: float | None, b: float | None, tolerance: float) -> float | None:
    if a is None or b is None:
        return None
    diff = abs(a - b)
    if diff <= tolerance:
        return 1.0 - (diff / tolerance) * 0.3  # small diffs still score near 1.0
    return 0.0


def _address_similarity(existing: Listing, incoming: NormalizedListing) -> float | None:
    if existing.postcode and incoming.postcode:
        if existing.postcode != incoming.postcode:
            return 0.0
        addr_sim = _text_similarity(existing.address, incoming.address)
        return 1.0 if addr_sim is None else max(0.5, addr_sim)
    return _text_similarity(existing.address, incoming.address)


def _image_overlap(existing: Listing, incoming: NormalizedListing) -> float | None:
    existing_names = {_filename(u) for u in (existing.images or [])}
    incoming_names = {_filename(u) for u in (incoming.images or [])}
    if not existing_names or not incoming_names:
        return None
    overlap = existing_names & incoming_names
    return len(overlap) / max(1, min(len(existing_names), len(incoming_names)))


def _filename(url: str) -> str:
    return re.sub(r"[?#].*$", "", url.rsplit("/", 1)[-1])


def similarity_score(existing: Listing, incoming: NormalizedListing) -> float:
    signals: dict[str, float] = {}

    if normalize_url(existing.canonical_url) == normalize_url(incoming.url):
        signals["url"] = 1.0

    addr_sim = _address_similarity(existing, incoming)
    if addr_sim is not None:
        signals["address"] = addr_sim

    rent_sim = _numeric_close(existing.rent_warm, incoming.rent_warm, tolerance=15)
    if rent_sim is not None:
        signals["rent"] = rent_sim

    size_sim = _numeric_close(existing.size_sqm, incoming.size_sqm, tolerance=2)
    if size_sim is not None:
        signals["size"] = size_sim

    if existing.rooms is not None and incoming.rooms is not None:
        signals["rooms"] = 1.0 if existing.rooms == incoming.rooms else 0.0

    title_sim = _text_similarity(existing.title, incoming.title)
    if title_sim is not None:
        signals["title"] = title_sim

    desc_sim = _text_similarity(existing.description, incoming.description)
    if desc_sim is not None:
        signals["description"] = desc_sim

    img_sim = _image_overlap(existing, incoming)
    if img_sim is not None:
        signals["images"] = img_sim

    if not signals:
        return 0.0

    total_weight = sum(_WEIGHTS[k] for k in signals)
    weighted_sum = sum(_WEIGHTS[k] * v for k, v in signals.items())
    return weighted_sum / total_weight


def find_existing_by_source_id(db: Session, source_key: str, source_listing_id: str) -> Listing | None:
    from app.models import ListingSourceRecord

    stmt = (
        select(Listing)
        .join(ListingSourceRecord)
        .where(
            ListingSourceRecord.source_key == source_key,
            ListingSourceRecord.source_listing_id == source_listing_id,
        )
    )
    return db.execute(stmt).scalars().first()


def find_duplicate(db: Session, incoming: NormalizedListing, candidates: list[Listing] | None = None) -> Listing | None:
    """Search for a cross-source duplicate among candidate listings (defaults
    to all listings in the same city, to keep the search space bounded)."""
    if candidates is None:
        stmt = select(Listing).where(Listing.city == incoming.city)
        candidates = list(db.execute(stmt).scalars().all())

    best_match: Listing | None = None
    best_score = 0.0
    for candidate in candidates:
        score = similarity_score(candidate, incoming)
        if score > best_score:
            best_score = score
            best_match = candidate

    if best_match is not None and best_score >= DUPLICATE_THRESHOLD:
        return best_match
    return None
