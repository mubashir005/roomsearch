"""Base class for sources that are implemented at the interface level but
disabled by default because the site's Terms of Service prohibit automated
access and/or no public API or RSS feed exists. Each concrete subclass
documents the specific reason so it's easy to review/reconsider later.
"""
from __future__ import annotations

from app.listing_schema import NormalizedListing
from app.sources.base import AccommodationSource, SourceHealthResult, SourceSearchResult


class DisabledSource(AccommodationSource):
    available = False
    unavailable_reason = "Not implemented."

    async def search(self, search_profile) -> SourceSearchResult:
        return SourceSearchResult(errors=[self.unavailable_reason or "Source disabled."])

    async def get_listing(self, url: str) -> NormalizedListing | None:
        return None

    async def health_check(self) -> SourceHealthResult:
        return SourceHealthResult(ok=False, status="disabled", message=self.unavailable_reason or "Source disabled.")
