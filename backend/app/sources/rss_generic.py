"""Generic RSS/Atom adapter.

Many accommodation portals and regional classifieds sites publish RSS/Atom
feeds for search results -- RSS is explicitly the preferred access method
(see task section 2: "prefer official APIs, then RSS feeds"). This adapter
works with ANY feed URL you configure via Source.config["feed_url"], so it
can be pointed at whichever legitimate feed you have access to without
writing new code.

Before fetching, it checks robots.txt for the feed's host and refuses to
proceed if disallowed.
"""
from __future__ import annotations

import time
from urllib import robotparser
from urllib.parse import urlparse

import feedparser
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.listing_schema import NormalizedListing
from app.matching import german_terms, price_parser
from app.matching.location import extract_district
from app.sources.base import AccommodationSource, SourceHealthResult, SourceSearchResult

USER_AGENT = "RoomSearchBot/1.0 (+personal accommodation search assistant; respects robots.txt)"


def _robots_allowed(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
    except Exception:
        # If robots.txt can't be fetched, err on the side of allowing --
        # absence of a robots.txt is not a prohibition.
        return True
    return rp.can_fetch(USER_AGENT, url)


class GenericRssSource(AccommodationSource):
    key = "rss_generic"
    display_name = "Generic RSS Feed"
    available = True

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def _fetch(self, url: str) -> str:
        async with httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT}, timeout=15.0, follow_redirects=True
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text

    async def search(self, search_profile) -> SourceSearchResult:
        feed_url = self.config.get("feed_url")
        result = SourceSearchResult()
        if not feed_url:
            result.errors.append("No feed_url configured for this source instance.")
            return result

        if not _robots_allowed(feed_url):
            result.errors.append(f"robots.txt disallows fetching {feed_url}; skipping.")
            return result

        start = time.monotonic()
        try:
            raw = await self._fetch(feed_url)
        except Exception as exc:  # noqa: BLE001 - surfaced to caller as a source error
            result.errors.append(f"Failed to fetch feed: {exc}")
            return result
        result.response_time_ms = int((time.monotonic() - start) * 1000)

        parsed = feedparser.parse(raw)
        result.found_count = len(parsed.entries)

        for entry in parsed.entries:
            try:
                listing = self._normalize_entry(entry)
                if listing:
                    result.listings.append(listing)
                    result.parsed_count += 1
            except Exception as exc:  # noqa: BLE001
                result.errors.append(f"Failed to parse entry '{getattr(entry, 'title', '?')}': {exc}")

        return result

    @staticmethod
    def _extract_images(entry) -> list[str]:
        """Pull listing photos out of whichever RSS/Atom image extension the
        feed happens to use -- media:content, media:thumbnail, or plain
        enclosures are all in common use across German classifieds feeds."""
        urls: list[str] = []

        for item in getattr(entry, "media_content", None) or []:
            url = item.get("url")
            if url:
                urls.append(url)

        for item in getattr(entry, "media_thumbnail", None) or []:
            url = item.get("url")
            if url:
                urls.append(url)

        for link in getattr(entry, "links", None) or []:
            link_type = link.get("type", "")
            if isinstance(link_type, str) and link_type.startswith("image/"):
                href = link.get("href")
                if href:
                    urls.append(href)

        # De-duplicate while preserving order.
        seen: set[str] = set()
        deduped = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                deduped.append(url)
        return deduped

    def _normalize_entry(self, entry) -> NormalizedListing | None:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        if not title or not link:
            return None

        summary = getattr(entry, "summary", "") or ""
        full_text = f"{title}\n{summary}"

        rent = price_parser.parse_rent(full_text)
        entry_id = getattr(entry, "id", None) or link

        return NormalizedListing(
            source_key=self.key,
            source_listing_id=entry_id,
            url=link,
            title=title,
            description=summary,
            district=extract_district(full_text),
            city="Hannover",
            rent_cold=rent.cold,
            rent_warm=rent.warm,
            rent_warm_is_estimated=rent.warm_is_estimated,
            utilities=rent.utilities,
            heating_cost=rent.heating,
            size_sqm=german_terms.extract_size_sqm(full_text),
            rooms=german_terms.extract_rooms(full_text),
            furnished=german_terms.extract_furnished(full_text),
            private_bathroom=german_terms.extract_private_bathroom(full_text),
            private_kitchen=german_terms.extract_private_kitchen(full_text),
            images=self._extract_images(entry),
            balcony=german_terms.extract_balcony(full_text),
            anmeldung=german_terms.extract_anmeldung(full_text),
            rental_type=german_terms.extract_rental_type(full_text),
            contact_url=link,
            raw_data={"feed_url": self.config.get("feed_url"), "entry": {k: str(v) for k, v in entry.items()}},
        )

    async def get_listing(self, url: str) -> NormalizedListing | None:
        # RSS feeds don't generally support single-item lookup by URL.
        return None

    async def health_check(self) -> SourceHealthResult:
        feed_url = self.config.get("feed_url")
        if not feed_url:
            return SourceHealthResult(ok=False, status="disabled", message="No feed_url configured.")
        if not _robots_allowed(feed_url):
            return SourceHealthResult(ok=False, status="error", message="Disallowed by robots.txt.")
        start = time.monotonic()
        try:
            raw = await self._fetch(feed_url)
        except Exception as exc:  # noqa: BLE001
            return SourceHealthResult(ok=False, status="error", message=str(exc))
        elapsed = int((time.monotonic() - start) * 1000)
        parsed = feedparser.parse(raw)
        if parsed.bozo and not parsed.entries:
            return SourceHealthResult(ok=False, status="error", message="Feed did not parse as RSS/Atom.", response_time_ms=elapsed)
        return SourceHealthResult(ok=True, status="ok", message=f"{len(parsed.entries)} entries", response_time_ms=elapsed)
