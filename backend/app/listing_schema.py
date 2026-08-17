"""Canonical intermediate listing representation shared by source adapters,
the matching engine, and the deduplication engine. Adapters normalize
whatever a source gives them into this shape; nothing downstream needs to
know which source a listing came from.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class NormalizedListing:
    source_key: str
    source_listing_id: str
    url: str

    title: str
    description: str | None = None

    address: str | None = None
    district: str | None = None
    city: str = "Hannover"
    postcode: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    rent_cold: float | None = None
    rent_warm: float | None = None
    rent_warm_is_estimated: bool = False
    utilities: float | None = None
    heating_cost: float | None = None
    deposit: float | None = None

    size_sqm: float | None = None
    rooms: float | None = None
    bathrooms: float | None = None
    floor: str | None = None

    furnished: str = "unknown"  # furnished | partially_furnished | unfurnished | unknown
    kitchen: bool | None = None
    private_kitchen: bool | None = None
    private_bathroom: bool | None = None
    balcony: bool | None = None

    anmeldung: str = "unknown"  # possible | impossible | unknown
    availability_date: datetime | None = None
    rental_type: str = "unknown"  # long_term | temporary | zwischenmiete | unknown

    contact_name: str | None = None
    contact_company: str | None = None
    contact_url: str | None = None

    images: list[str] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)
