"""Quick Add: user-submitted listing text runs through the same
scoring/dedup/notification pipeline as any automated source (task section
29's AI-fallback design, applied to manually-sourced content)."""
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.seed import run_seed

client = TestClient(app)

SAMPLE_TEXT = (
    "1-Zimmer-Wohnung in Hannover-List\n"
    "Warmmiete: 480 €, 32 m², möbliert, eigenes Bad, eigene Küche, Balkon vorhanden. "
    "Anmeldung möglich. Langfristig zu vermieten."
)


def _reset_ai(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")


def test_quick_add_creates_listing_from_text(db_session, monkeypatch):
    _reset_ai(monkeypatch)
    run_seed(db_session)

    resp = client.post("/api/listings/quick-add", json={"text": SAMPLE_TEXT, "url": "https://example.invalid/x1"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["is_new"] is True
    assert data["used_ai_fallback"] is False
    listing = data["listing"]
    assert listing["rent_warm"] == 480
    assert listing["size_sqm"] == 32
    assert listing["rooms"] == 1
    assert listing["furnished"] == "furnished"
    assert listing["anmeldung"] == "possible"
    assert listing["match_score"] > 0
    assert "manual" in [r["source_key"] for r in listing["source_records"]]
    get_settings.cache_clear()


def test_quick_add_registers_manual_source(db_session, monkeypatch):
    _reset_ai(monkeypatch)
    run_seed(db_session)
    client.post("/api/listings/quick-add", json={"text": SAMPLE_TEXT})

    resp = client.get("/api/sources")
    keys = [s["key"] for s in resp.json()]
    assert "manual" in keys
    get_settings.cache_clear()


def test_quick_add_idempotent_on_identical_resubmit(db_session, monkeypatch):
    _reset_ai(monkeypatch)
    run_seed(db_session)

    first = client.post("/api/listings/quick-add", json={"text": SAMPLE_TEXT})
    assert first.json()["is_new"] is True

    second = client.post("/api/listings/quick-add", json={"text": SAMPLE_TEXT})
    assert second.json()["is_new"] is False
    assert second.json()["listing"]["id"] == first.json()["listing"]["id"]
    get_settings.cache_clear()


def test_quick_add_dedupes_against_existing_source(db_session, monkeypatch):
    _reset_ai(monkeypatch)
    run_seed(db_session)

    # First, get the mock_demo source's "1-Zimmer-Wohnung in Hannover-List"
    # listing into the DB via a normal search run.
    client.post("/api/search/run")

    listings_before = client.get("/api/listings").json()
    assert listings_before["total"] == 4

    # Now quick-add a near-duplicate of that same apartment (different
    # wording, same address/rent/size) as if the user found it themselves
    # on a different site.
    near_dup_text = (
        "1 Zimmer Wohnung List Hannover - gemütlich\n"
        "Podbielskistraße 120, Warmmiete 480 €, 32 m², eigenes Bad, eigene Küche, Balkon."
    )
    resp = client.post(
        "/api/listings/quick-add",
        json={"text": near_dup_text, "url": "https://another-site.invalid/found-it"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_new"] is False  # merged into the existing canonical listing

    listings_after = client.get("/api/listings").json()
    assert listings_after["total"] == 4  # no net-new canonical listing created

    merged = next(l for l in listings_after["items"] if l["id"] == resp.json()["listing"]["id"])
    sources = {r["source_key"] for r in merged["source_records"]}
    assert sources == {"mock_demo", "manual"}
    get_settings.cache_clear()


def test_quick_add_with_ai_fallback_fills_gaps(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    run_seed(db_session)

    import json as jsonlib

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "choices": [
                    {
                        "message": {
                            "content": jsonlib.dumps(
                                {
                                    "rooms": 1,
                                    "rent_warm": 460,
                                    "district": "Nordstadt",
                                    "anmeldung": "possible",
                                }
                            )
                        }
                    }
                ]
            }

    class FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            return FakeResponse()

    import app.ai_parsing as ai_parsing_module

    monkeypatch.setattr(ai_parsing_module.httpx, "AsyncClient", FakeAsyncClient)

    # Vague text with no parseable rent/room count via regex -- deterministic
    # parsing should leave these unknown, AI fallback should fill them.
    vague_text = "Nice cozy place near the city, someone told me it's pretty central."
    resp = client.post("/api/listings/quick-add", json={"text": vague_text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["used_ai_fallback"] is True
    assert "rooms" in data["ai_fields_filled"]
    assert "rent_warm" in data["ai_fields_filled"]
    assert data["listing"]["rooms"] == 1
    assert data["listing"]["rent_warm"] == 460
    get_settings.cache_clear()
