from app.dedup.engine import content_hash, find_duplicate, find_existing_by_source_id, normalize_url, similarity_score
from app.listing_schema import NormalizedListing
from app.models import Listing, ListingSourceRecord


def make_normalized(**overrides) -> NormalizedListing:
    base = dict(
        source_key="wg_gesucht_test",
        source_listing_id="abc123",
        url="https://example.invalid/listing/abc123",
        title="1-Zimmer-Wohnung in Hannover-List",
        description="Schöne Wohnung mit Balkon, eigenes Bad.",
        address="Podbielskistraße 120",
        district="List",
        city="Hannover",
        postcode="30177",
        rent_warm=480,
        size_sqm=32,
        rooms=1,
    )
    base.update(overrides)
    return NormalizedListing(**base)


def make_db_listing(**overrides) -> Listing:
    base = dict(
        canonical_url="https://example.invalid/listing/abc123",
        content_hash="x",
        title="1-Zimmer-Wohnung in Hannover-List",
        description="Schöne Wohnung mit Balkon, eigenes Bad.",
        address="Podbielskistraße 120",
        district="List",
        city="Hannover",
        postcode="30177",
        rent_warm=480,
        size_sqm=32,
        rooms=1,
    )
    base.update(overrides)
    return Listing(**base)


def test_normalize_url_strips_query_and_trailing_slash():
    a = normalize_url("https://example.com/listing/1/?ref=abc&utm_source=x")
    b = normalize_url("https://EXAMPLE.com/listing/1")
    assert a == b


def test_content_hash_stable_for_identical_input():
    n1 = make_normalized()
    n2 = make_normalized()
    assert content_hash(n1) == content_hash(n2)


def test_content_hash_differs_when_rent_changes():
    n1 = make_normalized()
    n2 = make_normalized(rent_warm=520)
    assert content_hash(n1) != content_hash(n2)


def test_similarity_high_for_same_apartment_different_source():
    existing = make_db_listing()
    incoming = make_normalized(
        source_key="kleinanzeigen_test",
        source_listing_id="different-id",
        url="https://another-site.invalid/xyz",
        title="1 Zimmer Wohnung List Hannover - gemütlich",
        description="Gemütliche Wohnung mit Balkon und eigenem Bad.",
    )
    score = similarity_score(existing, incoming)
    assert score >= 0.6


def test_similarity_low_for_different_apartment():
    existing = make_db_listing()
    incoming = make_normalized(
        source_key="kleinanzeigen_test",
        source_listing_id="different-id",
        url="https://another-site.invalid/xyz",
        title="2 Zimmer Wohnung Garbsen",
        description="Große Wohnung außerhalb der Stadt.",
        address="Hauptstr. 10",
        district="Garbsen",
        city="Garbsen",
        postcode="30823",
        rent_warm=650,
        size_sqm=55,
        rooms=2,
    )
    score = similarity_score(existing, incoming)
    assert score < 0.6


def test_find_duplicate_merges_cross_source_listing(db_session):
    existing = make_db_listing()
    db_session.add(existing)
    db_session.flush()
    db_session.add(
        ListingSourceRecord(
            listing_id=existing.id,
            source_key="wg_gesucht_test",
            source_listing_id="abc123",
            url=existing.canonical_url,
        )
    )
    db_session.commit()

    incoming = make_normalized(
        source_key="kleinanzeigen_test",
        source_listing_id="different-id",
        url="https://another-site.invalid/xyz",
        title="1 Zimmer Wohnung List Hannover - gemütlich",
    )
    match = find_duplicate(db_session, incoming)
    assert match is not None
    assert match.id == existing.id


def test_find_existing_by_source_id(db_session):
    existing = make_db_listing()
    db_session.add(existing)
    db_session.flush()
    db_session.add(
        ListingSourceRecord(
            listing_id=existing.id,
            source_key="wg_gesucht_test",
            source_listing_id="abc123",
            url=existing.canonical_url,
        )
    )
    db_session.commit()

    found = find_existing_by_source_id(db_session, "wg_gesucht_test", "abc123")
    assert found is not None
    assert found.id == existing.id

    not_found = find_existing_by_source_id(db_session, "wg_gesucht_test", "nonexistent")
    assert not_found is None
