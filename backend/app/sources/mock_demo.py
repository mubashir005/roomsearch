"""Mock/demo source: deterministic fixture data used to exercise the full
pipeline (search -> normalize -> filter -> dedupe -> store -> notify)
without depending on any external website. Useful for local development,
tests, and demoing the app before you have a real RSS feed configured.

Enabled by default so `docker compose up` produces visible results
immediately; disable it once real sources are configured.
"""
from __future__ import annotations

import time
from datetime import datetime

from app.listing_schema import NormalizedListing
from app.sources.base import AccommodationSource, SourceHealthResult, SourceSearchResult

_FIXTURES = [
    dict(
        source_listing_id="demo-1001",
        url="https://example-listings.invalid/demo-1001",
        title="1-Zimmer-Wohnung in Hannover-List",
        description=(
            "Schöne, möblierte 1-Zimmer-Wohnung im Herzen von List. Eigenes Bad, eigene Küche, "
            "Balkon vorhanden. Anmeldung möglich. Warmmiete: 480 € (Kaltmiete 400 €, Nebenkosten 80 €). "
            "32 m², langfristig zu vermieten."
        ),
        address="Podbielskistraße 120",
        district="List",
        city="Hannover",
        postcode="30177",
        rent_cold=400,
        rent_warm=480,
        rent_warm_is_estimated=False,
        size_sqm=32,
        rooms=1,
        furnished="furnished",
        private_bathroom=True,
        private_kitchen=True,
        balcony=True,
        anmeldung="possible",
        availability_date=datetime(2026, 10, 1),
        rental_type="long_term",
        images=[
            "https://picsum.photos/seed/demo-1001-a/800/600",
            "https://picsum.photos/seed/demo-1001-b/800/600",
            "https://picsum.photos/seed/demo-1001-c/800/600",
        ],
    ),
    dict(
        source_listing_id="demo-1002",
        url="https://example-listings.invalid/demo-1002",
        title="Studio Apartment Vahrenwald - unmöbliert",
        description=(
            "Kompaktes Studio in Vahrenwald, unmöbliert. Gemeinsame Küche. Kaltmiete 380 €, "
            "Nebenkosten 60 €, Heizkosten 40 €. Anmeldung nicht möglich (Zwischenmiete)."
        ),
        address="Vahrenwalder Str. 55",
        district="Vahrenwald",
        city="Hannover",
        postcode="30165",
        rent_cold=380,
        size_sqm=24,
        rooms=1,
        furnished="unfurnished",
        private_bathroom=True,
        private_kitchen=False,
        balcony=False,
        anmeldung="impossible",
        availability_date=datetime(2026, 9, 1),
        rental_type="zwischenmiete",
        images=[
            "https://picsum.photos/seed/demo-1002-a/800/600",
            "https://picsum.photos/seed/demo-1002-b/800/600",
        ],
    ),
    dict(
        source_listing_id="demo-1003",
        url="https://example-listings.invalid/demo-1003",
        title="Einzimmerwohnung Suedstadt teilmöbliert",
        description=(
            "Gemütliche Einzimmerwohnung in der Südstadt, teilmöbliert, eigenes Bad. "
            "Warmmiete 495 €. Anmeldung möglich. 28 m²."
        ),
        address="Hildesheimer Str. 200",
        district="Südstadt",
        city="Hannover",
        postcode="30173",
        rent_warm=495,
        size_sqm=28,
        rooms=1,
        furnished="partially_furnished",
        private_bathroom=True,
        private_kitchen=True,
        balcony=False,
        anmeldung="possible",
        availability_date=datetime(2026, 10, 15),
        rental_type="long_term",
        images=[
            "https://picsum.photos/seed/demo-1003-a/800/600",
            "https://picsum.photos/seed/demo-1003-b/800/600",
            "https://picsum.photos/seed/demo-1003-c/800/600",
        ],
    ),
    dict(
        source_listing_id="demo-1004",
        url="https://example-listings.invalid/demo-1004",
        title="2-Zimmer-Wohnung Garbsen",
        description="Größere Wohnung außerhalb des Budgets, Kaltmiete 650 €, keine Nebenkosten angegeben.",
        address="Hauptstr. 10",
        district="Garbsen",
        city="Garbsen",
        postcode="30823",
        rent_cold=650,
        size_sqm=55,
        rooms=2,
        furnished="unknown",
        anmeldung="unknown",
        rental_type="long_term",
        images=[],
    ),
]


class MockDemoSource(AccommodationSource):
    key = "mock_demo"
    display_name = "Mock/Demo Source (fixture data)"
    available = True

    async def search(self, search_profile) -> SourceSearchResult:
        start = time.monotonic()
        result = SourceSearchResult()
        for fixture in _FIXTURES:
            full_text = f"{fixture['title']} {fixture['description']}"
            from app.matching import price_parser

            rent = price_parser.parse_rent(
                full_text,
                cold=fixture.get("rent_cold"),
                warm=fixture.get("rent_warm"),
            )
            listing = NormalizedListing(
                source_key=self.key,
                source_listing_id=fixture["source_listing_id"],
                url=fixture["url"],
                title=fixture["title"],
                description=fixture["description"],
                address=fixture.get("address"),
                district=fixture.get("district"),
                city=fixture.get("city", "Hannover"),
                postcode=fixture.get("postcode"),
                rent_cold=rent.cold,
                rent_warm=rent.warm,
                rent_warm_is_estimated=rent.warm_is_estimated,
                utilities=rent.utilities,
                heating_cost=rent.heating,
                size_sqm=fixture.get("size_sqm"),
                rooms=fixture.get("rooms"),
                furnished=fixture.get("furnished", "unknown"),
                private_bathroom=fixture.get("private_bathroom"),
                private_kitchen=fixture.get("private_kitchen"),
                balcony=fixture.get("balcony"),
                anmeldung=fixture.get("anmeldung", "unknown"),
                availability_date=fixture.get("availability_date"),
                rental_type=fixture.get("rental_type", "unknown"),
                contact_url=fixture["url"],
                images=fixture.get("images", []),
                raw_data={"fixture": True},
            )
            result.listings.append(listing)
            result.parsed_count += 1
        result.found_count = len(_FIXTURES)
        result.response_time_ms = int((time.monotonic() - start) * 1000)
        return result

    async def get_listing(self, url: str) -> NormalizedListing | None:
        for fixture in _FIXTURES:
            if fixture["url"] == url:
                search_result = await self.search(None)
                for listing in search_result.listings:
                    if listing.url == url:
                        return listing
        return None

    async def health_check(self) -> SourceHealthResult:
        return SourceHealthResult(ok=True, status="ok", message="Mock source always healthy.", response_time_ms=1)
