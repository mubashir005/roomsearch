import asyncio

import feedparser

from app.sources.disabled import DisabledSource
from app.sources.mock_demo import MockDemoSource
from app.sources.registry import SOURCE_REGISTRY
from app.sources.rss_generic import GenericRssSource
from app.sources.wg_gesucht import WgGesuchtSource


def test_mock_demo_source_returns_fixtures():
    source = MockDemoSource()
    result = asyncio.run(source.search(None))
    assert result.found_count == 4
    assert result.parsed_count == 4
    assert len(result.listings) == 4


def test_mock_demo_source_includes_images_when_available():
    source = MockDemoSource()
    result = asyncio.run(source.search(None))
    with_images = next(l for l in result.listings if l.source_listing_id == "demo-1001")
    assert len(with_images.images) == 3
    assert all(url.startswith("https://") for url in with_images.images)

    without_images = next(l for l in result.listings if l.source_listing_id == "demo-1004")
    assert without_images.images == []


def test_mock_demo_source_derives_estimated_warm_rent():
    source = MockDemoSource()
    result = asyncio.run(source.search(None))
    listing = next(l for l in result.listings if l.source_listing_id == "demo-1002")
    # cold 380 + nebenkosten 60 + heizkosten 40 = 480, derived -> estimated
    assert listing.rent_warm == 480
    assert listing.rent_warm_is_estimated is True


def test_mock_demo_source_direct_warm_rent_not_estimated():
    source = MockDemoSource()
    result = asyncio.run(source.search(None))
    listing = next(l for l in result.listings if l.source_listing_id == "demo-1001")
    assert listing.rent_warm == 480
    assert listing.rent_warm_is_estimated is False


def test_mock_demo_health_check():
    source = MockDemoSource()
    health = asyncio.run(source.health_check())
    assert health.ok is True
    assert health.status == "ok"


def test_disabled_sources_report_unavailable():
    source = WgGesuchtSource()
    assert source.available is False
    assert source.unavailable_reason
    result = asyncio.run(source.search(None))
    assert result.listings == []
    assert result.errors
    health = asyncio.run(source.health_check())
    assert health.ok is False
    assert health.status == "disabled"


def test_all_disabled_sources_subclass_disabled_source():
    for key, cls in SOURCE_REGISTRY.items():
        if key in ("mock_demo", "rss_generic", "meinestadt"):
            continue
        assert issubclass(cls, DisabledSource), f"{key} should be a DisabledSource subclass"
        assert cls.available is False
        assert cls.unavailable_reason


def test_generic_rss_source_without_feed_url_errors_cleanly_no_network():
    source = GenericRssSource()
    result = asyncio.run(source.search(None))
    assert result.listings == []
    assert result.errors
    health = asyncio.run(source.health_check())
    assert health.ok is False


def test_generic_rss_source_normalizes_entry_without_network():
    source = GenericRssSource(config={"feed_url": "https://example.invalid/feed.xml"})
    entry = feedparser.FeedParserDict(
        {
            "title": "1-Zimmer-Wohnung Hannover List, Warmmiete 480 €, 32 m², möbliert, Anmeldung möglich",
            "link": "https://example.invalid/listing/1",
            "summary": "Schöne Wohnung mit Balkon, eigenes Bad, eigene Küche.",
            "id": "entry-1",
        }
    )
    normalized = source._normalize_entry(entry)
    assert normalized is not None
    assert normalized.rent_warm == 480
    assert normalized.size_sqm == 32
    assert normalized.rooms == 1.0
    assert normalized.furnished == "furnished"
    assert normalized.anmeldung == "possible"
    assert normalized.private_bathroom is True
    assert normalized.private_kitchen is True
    assert normalized.balcony is True


def test_generic_rss_source_extracts_images_from_media_extensions():
    source = GenericRssSource(config={"feed_url": "https://example.invalid/feed.xml"})
    entry = feedparser.FeedParserDict(
        {
            "title": "1-Zimmer-Wohnung Hannover List",
            "link": "https://example.invalid/listing/2",
            "summary": "Schöne Wohnung.",
            "id": "entry-2",
            "media_content": [{"url": "https://example.invalid/img/a.jpg"}],
            "media_thumbnail": [{"url": "https://example.invalid/img/thumb.jpg"}],
            "links": [
                {"href": "https://example.invalid/listing/2", "type": "text/html"},
                {"href": "https://example.invalid/img/b.jpg", "type": "image/jpeg"},
            ],
        }
    )
    normalized = source._normalize_entry(entry)
    assert normalized is not None
    assert normalized.images == [
        "https://example.invalid/img/a.jpg",
        "https://example.invalid/img/thumb.jpg",
        "https://example.invalid/img/b.jpg",
    ]


def test_generic_rss_source_no_images_when_none_present():
    source = GenericRssSource(config={"feed_url": "https://example.invalid/feed.xml"})
    entry = feedparser.FeedParserDict(
        {
            "title": "Studio ohne Bilder",
            "link": "https://example.invalid/listing/3",
            "summary": "Keine Fotos vorhanden.",
            "id": "entry-3",
        }
    )
    normalized = source._normalize_entry(entry)
    assert normalized is not None
    assert normalized.images == []


def test_source_registry_contains_all_documented_sources():
    expected_keys = {
        "mock_demo", "rss_generic", "meinestadt", "wg_gesucht", "kleinanzeigen",
        "immoscout24", "immowelt", "immonet", "housinganywhere", "wunderflats",
    }
    assert expected_keys.issubset(SOURCE_REGISTRY.keys())
