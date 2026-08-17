"""Configurable 0-100 match scoring, per task section 4."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.listing_schema import NormalizedListing
from app.matching.location import LocationMatch, classify_location

DEFAULT_WEIGHTS: dict[str, int] = {
    "price_under_400": 25,
    "price_400_to_500": 20,
    "core_district": 20,
    "hannover_general": 10,
    "one_room_studio": 15,
    "preferred_size": 10,
    "anmeldung_confirmed": 10,
    "furnished": 8,
    "partially_furnished": 4,
    "private_bathroom": 5,
    "private_kitchen": 5,
    "balcony": 5,
    "available_october_2026": 5,
    "long_term": 3,
    # penalties (all negative)
    "penalty_over_budget": -30,
    "penalty_anmeldung_impossible": -20,
    "penalty_shared_bathroom": -15,
    "penalty_shared_kitchen": -15,
    "penalty_temporary": -10,
    "penalty_outside_hannover": -10,
    "penalty_missing_rent": -10,
}

TARGET_AVAILABILITY = datetime(2026, 10, 1)


@dataclass
class ScoreResult:
    score: int
    reasons: list[str] = field(default_factory=list)  # "✓ ..." positive matches
    warnings: list[str] = field(default_factory=list)  # "✗ ..." penalties applied


def score_listing(
    listing: NormalizedListing,
    *,
    max_rent_warm: float = 500,
    preferred_size_min: float = 20,
    preferred_size_max: float = 50,
    weights: dict[str, int] | None = None,
) -> ScoreResult:
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    score = 0
    reasons: list[str] = []
    warnings: list[str] = []

    # --- Price ---
    if listing.rent_warm is not None:
        if listing.rent_warm <= max_rent_warm:
            if listing.rent_warm <= 400:
                score += w["price_under_400"]
                reasons.append(f"Warm rent €{listing.rent_warm:.0f} <= €400")
            else:
                score += w["price_400_to_500"]
                reasons.append(f"Warm rent €{listing.rent_warm:.0f} <= €{max_rent_warm:.0f}")
        else:
            score += w["penalty_over_budget"]
            warnings.append(f"Warm rent €{listing.rent_warm:.0f} > €{max_rent_warm:.0f}")
    else:
        score += w["penalty_missing_rent"]
        warnings.append("Warmmiete unknown / missing rent information")

    # --- Location ---
    loc = classify_location(listing.city, listing.district, listing.address or "")
    if loc == LocationMatch.IN_CORE_DISTRICT:
        score += w["core_district"]
        reasons.append(f"Hannover core district ({listing.district or 'match'})")
    elif loc == LocationMatch.IN_HANNOVER:
        score += w["hannover_general"]
        reasons.append("Hannover")
    elif loc == LocationMatch.NEARBY:
        reasons.append(f"Nearby area ({listing.district or listing.city})")
    elif loc == LocationMatch.OUTSIDE:
        score += w["penalty_outside_hannover"]
        warnings.append("Outside Hannover / nearby areas")

    # --- Rooms ---
    if listing.rooms is not None and listing.rooms <= 1.5:
        score += w["one_room_studio"]
        reasons.append(f"{listing.rooms:g} room(s) / studio")

    # --- Size ---
    if listing.size_sqm is not None and preferred_size_min <= listing.size_sqm <= preferred_size_max:
        score += w["preferred_size"]
        reasons.append(f"{listing.size_sqm:g} m² (preferred range)")

    # --- Anmeldung ---
    if listing.anmeldung == "possible":
        score += w["anmeldung_confirmed"]
        reasons.append("Anmeldung possible")
    elif listing.anmeldung == "impossible":
        score += w["penalty_anmeldung_impossible"]
        warnings.append("Anmeldung explicitly impossible")

    # --- Furnished ---
    if listing.furnished == "furnished":
        score += w["furnished"]
        reasons.append("Furnished")
    elif listing.furnished == "partially_furnished":
        score += w["partially_furnished"]
        reasons.append("Partially furnished")

    # --- Bathroom / kitchen ---
    if listing.private_bathroom is True:
        score += w["private_bathroom"]
        reasons.append("Private bathroom")
    elif listing.private_bathroom is False:
        score += w["penalty_shared_bathroom"]
        warnings.append("Shared bathroom")

    if listing.private_kitchen is True:
        score += w["private_kitchen"]
        reasons.append("Private kitchen")
    elif listing.private_kitchen is False:
        score += w["penalty_shared_kitchen"]
        warnings.append("Shared kitchen")

    # --- Balcony ---
    if listing.balcony:
        score += w["balcony"]
        reasons.append("Balcony")

    # --- Availability ---
    if listing.availability_date is not None:
        if listing.availability_date <= TARGET_AVAILABILITY:
            score += w["available_october_2026"]
            reasons.append(f"Available {listing.availability_date.strftime('%B %Y')}")
        else:
            reasons.append(f"Available {listing.availability_date.strftime('%d.%m.%Y')} (later than target)")

    # --- Rental type ---
    if listing.rental_type == "long_term":
        score += w["long_term"]
        reasons.append("Long-term rental")
    elif listing.rental_type == "temporary":
        score += w["penalty_temporary"]
        warnings.append("Temporary only")
    elif listing.rental_type == "zwischenmiete":
        score += w["penalty_temporary"]
        warnings.append("Zwischenmiete (lower priority)")

    score = max(0, min(100, score))
    return ScoreResult(score=score, reasons=reasons, warnings=warnings)
