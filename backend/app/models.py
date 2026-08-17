"""SQLAlchemy ORM models."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class ListingStatus(str, enum.Enum):
    NEW = "NEW"
    MATCHED = "MATCHED"
    NOTIFIED = "NOTIFIED"
    UPDATED = "UPDATED"
    EXPIRED = "EXPIRED"
    REMOVED = "REMOVED"
    REJECTED = "REJECTED"


class FurnishedStatus(str, enum.Enum):
    FURNISHED = "furnished"
    PARTIALLY = "partially_furnished"
    UNFURNISHED = "unfurnished"
    UNKNOWN = "unknown"


class AnmeldungStatus(str, enum.Enum):
    POSSIBLE = "possible"
    IMPOSSIBLE = "impossible"
    UNKNOWN = "unknown"


class RentalType(str, enum.Enum):
    LONG_TERM = "long_term"
    TEMPORARY = "temporary"
    ZWISCHENMIETE = "zwischenmiete"
    UNKNOWN = "unknown"


class SourceStatus(str, enum.Enum):
    OK = "ok"
    LIMITED = "limited"
    ERROR = "error"
    DISABLED = "disabled"


# ---------------------------------------------------------------------------
# Source (adapter registry + admin/health state)
# ---------------------------------------------------------------------------
class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)  # matches adapter registry key
    name: Mapped[str] = mapped_column(String(128))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    config: Mapped[dict] = mapped_column(JSON, default=dict)  # e.g. {"feed_url": "..."}

    status: Mapped[SourceStatus] = mapped_column(Enum(SourceStatus), default=SourceStatus.DISABLED)
    unavailable_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_listings_found: Mapped[int] = mapped_column(Integer, default=0)
    last_matching_found: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# Search profile (configurable criteria + scoring weights + notification prefs)
# ---------------------------------------------------------------------------
class SearchProfile(Base):
    __tablename__ = "search_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    city: Mapped[str] = mapped_column(String(64), default="Hannover")
    preferred_districts: Mapped[list] = mapped_column(JSON, default=list)
    nearby_areas: Mapped[list] = mapped_column(JSON, default=list)

    max_rent_warm: Mapped[float] = mapped_column(Float, default=500)
    min_size_sqm: Mapped[float] = mapped_column(Float, default=15)
    preferred_size_min: Mapped[float] = mapped_column(Float, default=20)
    preferred_size_max: Mapped[float] = mapped_column(Float, default=50)
    max_rooms: Mapped[float] = mapped_column(Float, default=1)

    available_from: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    anmeldung_preference: Mapped[str] = mapped_column(String(32), default="preferred")

    notification_mode: Mapped[str] = mapped_column(String(32), default="immediate")
    email_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    min_score_to_notify: Mapped[int] = mapped_column(Integer, default=50)

    # scoring weights, configurable from admin UI. See app.matching.scoring for defaults/keys.
    scoring_weights: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


# ---------------------------------------------------------------------------
# Listing (canonical record) + raw per-source records
# ---------------------------------------------------------------------------
class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # canonical / dedup identity
    canonical_url: Mapped[str] = mapped_column(String(1024))
    content_hash: Mapped[str] = mapped_column(String(64), index=True)

    # primary display fields (from best/most-complete source record)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(256), nullable=True)
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    city: Mapped[str] = mapped_column(String(64), default="Hannover")
    postcode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    rent_cold: Mapped[float | None] = mapped_column(Float, nullable=True)
    rent_warm: Mapped[float | None] = mapped_column(Float, nullable=True)
    rent_warm_is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    utilities: Mapped[float | None] = mapped_column(Float, nullable=True)
    heating_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    deposit: Mapped[float | None] = mapped_column(Float, nullable=True)

    size_sqm: Mapped[float | None] = mapped_column(Float, nullable=True)
    rooms: Mapped[float | None] = mapped_column(Float, nullable=True)
    bathrooms: Mapped[float | None] = mapped_column(Float, nullable=True)
    floor: Mapped[str | None] = mapped_column(String(32), nullable=True)

    furnished: Mapped[FurnishedStatus] = mapped_column(Enum(FurnishedStatus), default=FurnishedStatus.UNKNOWN)
    kitchen: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    private_kitchen: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    private_bathroom: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    balcony: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    anmeldung: Mapped[AnmeldungStatus] = mapped_column(Enum(AnmeldungStatus), default=AnmeldungStatus.UNKNOWN)
    availability_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rental_type: Mapped[RentalType] = mapped_column(Enum(RentalType), default=RentalType.UNKNOWN)

    contact_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    contact_company: Mapped[str | None] = mapped_column(String(128), nullable=True)
    contact_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    images: Mapped[list] = mapped_column(JSON, default=list)

    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_changed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notification_count: Mapped[int] = mapped_column(Integer, default=0)

    match_score: Mapped[int] = mapped_column(Integer, default=0)
    match_explanation: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), default=ListingStatus.NEW)

    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    source_records: Mapped[list["ListingSourceRecord"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )

    @property
    def sources_found_on(self) -> list[str]:
        return sorted({r.source_key for r in self.source_records})


class ListingSourceRecord(Base):
    """One raw sighting of a listing on a specific source, linked to a canonical Listing."""

    __tablename__ = "listing_source_records"
    __table_args__ = (UniqueConstraint("source_key", "source_listing_id", name="uq_source_listing"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)

    source_key: Mapped[str] = mapped_column(String(64), index=True)
    source_listing_id: Mapped[str] = mapped_column(String(256))
    url: Mapped[str] = mapped_column(String(1024))

    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict)

    listing: Mapped["Listing"] = relationship(back_populates="source_records")


# ---------------------------------------------------------------------------
# Run history / per-source run logs
# ---------------------------------------------------------------------------
class SearchRun(Base):
    __tablename__ = "search_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trigger: Mapped[str] = mapped_column(String(32), default="scheduled")  # scheduled | manual

    total_discovered: Mapped[int] = mapped_column(Integer, default=0)
    total_parsed: Mapped[int] = mapped_column(Integer, default=0)
    total_matching: Mapped[int] = mapped_column(Integer, default=0)
    total_new: Mapped[int] = mapped_column(Integer, default=0)
    total_duplicates_merged: Mapped[int] = mapped_column(Integer, default=0)

    source_results: Mapped[list] = mapped_column(JSON, default=list)
    errors: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


# ---------------------------------------------------------------------------
# Notifications (dashboard feed / read state)
# ---------------------------------------------------------------------------
class NotificationLog(Base):
    __tablename__ = "notification_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int | None] = mapped_column(ForeignKey("listings.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(32))  # email | telegram | dashboard
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
