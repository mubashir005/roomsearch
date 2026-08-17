from datetime import datetime

from app.listing_schema import NormalizedListing
from app.matching.scoring import score_listing


def make_listing(**overrides) -> NormalizedListing:
    base = dict(
        source_key="mock_demo",
        source_listing_id="1",
        url="https://example.invalid/1",
        title="1-Zimmer-Wohnung",
        city="Hannover",
        district="List",
        rent_warm=480,
        size_sqm=32,
        rooms=1,
        furnished="furnished",
        private_bathroom=True,
        private_kitchen=True,
        balcony=True,
        anmeldung="possible",
        availability_date=datetime(2026, 10, 1),
        rental_type="long_term",
    )
    base.update(overrides)
    return NormalizedListing(**base)


def test_high_quality_listing_scores_highly():
    result = score_listing(make_listing())
    assert result.score >= 90
    assert any("Warm rent" in r for r in result.reasons)
    assert any("core district" in r.lower() for r in result.reasons)


def test_over_budget_is_penalized():
    result = score_listing(make_listing(rent_warm=650))
    assert any("650" in w for w in result.warnings)
    cheap = score_listing(make_listing(rent_warm=480))
    assert result.score < cheap.score


def test_missing_rent_is_penalized_not_ignored():
    result = score_listing(make_listing(rent_warm=None))
    assert any("unknown" in w.lower() or "missing" in w.lower() for w in result.warnings)


def test_anmeldung_impossible_is_strongly_penalized():
    possible = score_listing(make_listing(anmeldung="possible"))
    impossible = score_listing(make_listing(anmeldung="impossible"))
    assert impossible.score < possible.score
    assert any("impossible" in w.lower() for w in impossible.warnings)


def test_shared_bathroom_and_kitchen_penalized():
    result = score_listing(make_listing(private_bathroom=False, private_kitchen=False))
    assert any("shared bathroom" in w.lower() for w in result.warnings)
    assert any("shared kitchen" in w.lower() for w in result.warnings)


def test_outside_hannover_penalized():
    result = score_listing(make_listing(city="Berlin", district=None))
    assert any("outside" in w.lower() for w in result.warnings)


def test_score_clamped_between_0_and_100():
    result = score_listing(
        make_listing(
            rent_warm=1000, anmeldung="impossible", private_bathroom=False, private_kitchen=False,
            rental_type="temporary", city="Berlin", district=None,
        )
    )
    assert 0 <= result.score <= 100


def test_custom_weights_are_applied():
    default_result = score_listing(make_listing())
    custom_result = score_listing(make_listing(), weights={"core_district": 0})
    assert custom_result.score < default_result.score
