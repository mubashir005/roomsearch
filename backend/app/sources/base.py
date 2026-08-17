"""Common interface every accommodation source adapter implements.

Adding a new source means writing one class here and registering it in
`registry.py` -- nothing else in the application needs to change.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.listing_schema import NormalizedListing


@dataclass
class SourceSearchResult:
    listings: list[NormalizedListing] = field(default_factory=list)
    found_count: int = 0
    parsed_count: int = 0
    errors: list[str] = field(default_factory=list)
    response_time_ms: int | None = None


@dataclass
class SourceHealthResult:
    ok: bool
    status: str  # ok | limited | error | disabled
    message: str = ""
    response_time_ms: int | None = None


class AccommodationSource(ABC):
    """Base class for a source adapter.

    `key` must be a stable, unique, machine-friendly identifier (used as the
    Source.key DB column and for ListingSourceRecord.source_key).
    """

    key: str = "base"
    display_name: str = "Base Source"

    #: Whether this adapter is legally/technically able to run. Sources that
    #: are disabled per the project's legal/ToS rules (see README) should set
    #: this to False and populate `unavailable_reason`.
    available: bool = True
    unavailable_reason: str | None = None

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    async def search(self, search_profile) -> SourceSearchResult:
        """Search this source using the given SearchProfile ORM object (or a
        compatible object exposing the same attributes) and return
        normalized listings."""
        raise NotImplementedError

    @abstractmethod
    async def get_listing(self, url: str) -> NormalizedListing | None:
        """Fetch and normalize a single listing by URL, if supported."""
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> SourceHealthResult:
        """Lightweight check that the source is reachable/usable."""
        raise NotImplementedError
