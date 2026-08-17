"""Pydantic request/response schemas for the API."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ListingSourceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    source_key: str
    url: str
    first_seen_at: datetime
    last_seen_at: datetime


class ListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_url: str
    title: str
    description: str | None
    address: str | None
    district: str | None
    city: str
    postcode: str | None
    latitude: float | None
    longitude: float | None

    rent_cold: float | None
    rent_warm: float | None
    rent_warm_is_estimated: bool
    utilities: float | None
    heating_cost: float | None
    deposit: float | None

    size_sqm: float | None
    rooms: float | None
    bathrooms: float | None
    floor: str | None

    furnished: str
    kitchen: bool | None
    private_kitchen: bool | None
    private_bathroom: bool | None
    balcony: bool | None

    anmeldung: str
    availability_date: datetime | None
    rental_type: str

    contact_name: str | None
    contact_company: str | None
    contact_url: str | None

    images: list[str]

    first_seen_at: datetime
    last_seen_at: datetime
    last_changed_at: datetime
    notified_at: datetime | None
    notification_count: int

    match_score: int
    match_explanation: list[str]
    status: str

    source_records: list[ListingSourceRecordOut]

    @property
    def sources_found_on(self) -> list[str]:
        return sorted({r.source_key for r in self.source_records})


class ListingListOut(BaseModel):
    total: int
    items: list[ListingOut]


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    name: str
    enabled: bool
    priority: int
    config: dict
    status: str
    unavailable_reason: str | None
    last_success_at: datetime | None
    last_error_at: datetime | None
    last_error: str | None
    last_response_time_ms: int | None
    last_listings_found: int
    last_matching_found: int


class SourceUpdateIn(BaseModel):
    enabled: bool | None = None
    priority: int | None = None
    config: dict | None = None


class SearchProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    active: bool
    city: str
    preferred_districts: list[str]
    nearby_areas: list[str]
    max_rent_warm: float
    min_size_sqm: float
    preferred_size_min: float
    preferred_size_max: float
    max_rooms: float
    available_from: datetime | None
    anmeldung_preference: str
    notification_mode: str
    email_enabled: bool
    telegram_enabled: bool
    min_score_to_notify: int
    scoring_weights: dict


class SearchProfileIn(BaseModel):
    name: str
    active: bool = True
    city: str = "Hannover"
    preferred_districts: list[str] = []
    nearby_areas: list[str] = []
    max_rent_warm: float = 500
    min_size_sqm: float = 15
    preferred_size_min: float = 20
    preferred_size_max: float = 50
    max_rooms: float = 1
    available_from: datetime | None = None
    anmeldung_preference: str = "preferred"
    notification_mode: str = "immediate"
    email_enabled: bool = True
    telegram_enabled: bool = False
    min_score_to_notify: int = 50
    scoring_weights: dict = {}


class SearchRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    started_at: datetime
    finished_at: datetime | None
    trigger: str
    total_discovered: int
    total_parsed: int
    total_matching: int
    total_new: int
    total_duplicates_merged: int
    source_results: list[dict]
    errors: list[dict]


class NotificationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    listing_id: int | None
    channel: str
    subject: str | None
    body_preview: str | None
    success: bool
    error: str | None
    read: bool
    created_at: datetime


class DashboardStatsOut(BaseModel):
    new_today: int
    high_priority: int
    under_400: int
    between_400_and_500: int
    anmeldung_confirmed: int
    furnished: int
    unseen: int
    sources_online: int
    sources_total: int
