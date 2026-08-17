"""Hannover district / area matching."""
from __future__ import annotations

CORE_DISTRICTS = [
    "List",
    "Vahrenwald",
    "Vahrenwald-List",
    "Nordstadt",
    "Oststadt",
    "Südstadt",
    "Mitte",
    "Linden",
    "Linden-Mitte",
    "Linden-Nord",
    "Linden-Süd",
    "Calenberger Neustadt",
    "Herrenhausen",
    "Hainholz",
    "Bothfeld",
    "Döhren",
]

NEARBY_AREAS = ["Garbsen", "Langenhagen", "Laatzen", "Seelze"]


def _normalize(s: str) -> str:
    return (
        s.strip()
        .lower()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )


_CORE_NORMALIZED = {_normalize(d) for d in CORE_DISTRICTS}
_NEARBY_NORMALIZED = {_normalize(d) for d in NEARBY_AREAS}

# Ordered, longest-normalized-form-first so e.g. "Vahrenwald-List" is matched
# before the shorter "Vahrenwald"/"List" when all three are present.
_CORE_ORDERED = sorted({(_normalize(d), d) for d in CORE_DISTRICTS}, key=lambda pair: -len(pair[0]))
_NEARBY_ORDERED = sorted({(_normalize(a), a) for a in NEARBY_AREAS}, key=lambda pair: -len(pair[0]))


class LocationMatch:
    IN_CORE_DISTRICT = "core_district"
    IN_HANNOVER = "hannover"
    NEARBY = "nearby"
    OUTSIDE = "outside"
    UNKNOWN = "unknown"


def classify_location(city: str | None, district: str | None, text: str = "") -> str:
    """Classify a listing's location relative to the search area."""
    haystack = _normalize(f"{city or ''} {district or ''} {text or ''}")
    if not haystack.strip():
        return LocationMatch.UNKNOWN

    for d in _CORE_NORMALIZED:
        if d and d in haystack:
            return LocationMatch.IN_CORE_DISTRICT

    if "hannover" in haystack:
        return LocationMatch.IN_HANNOVER

    for a in _NEARBY_NORMALIZED:
        if a and a in haystack:
            return LocationMatch.NEARBY

    return LocationMatch.OUTSIDE


def extract_district(text: str) -> str | None:
    haystack = _normalize(text or "")
    for normalized, original in _CORE_ORDERED:
        if normalized and normalized in haystack:
            return original
    for normalized, original in _NEARBY_ORDERED:
        if normalized and normalized in haystack:
            return original
    return None
