"""API integration tests using FastAPI's TestClient against the SQLite test
database configured in conftest.py."""
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.seed import run_seed

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_api_key_not_required_when_unset(db_session):
    get_settings.cache_clear()
    resp = client.get("/api/sources")
    assert resp.status_code == 200
    get_settings.cache_clear()


def test_api_key_required_when_set(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("API_KEY", "test-secret-key-123")

    unauthenticated = client.get("/api/sources")
    assert unauthenticated.status_code == 401

    wrong_key = client.get("/api/sources", headers={"X-API-Key": "wrong"})
    assert wrong_key.status_code == 401

    correct_key = client.get("/api/sources", headers={"X-API-Key": "test-secret-key-123"})
    assert correct_key.status_code == 200

    # /api/health always stays open, even with API_KEY set.
    health = client.get("/api/health")
    assert health.status_code == 200

    get_settings.cache_clear()


def test_seed_then_list_sources(db_session):
    run_seed(db_session)
    resp = client.get("/api/sources")
    assert resp.status_code == 200
    data = resp.json()
    keys = {s["key"] for s in data}
    assert "mock_demo" in keys
    assert "wg_gesucht" in keys
    mock_source = next(s for s in data if s["key"] == "mock_demo")
    assert mock_source["enabled"] is True
    wg_source = next(s for s in data if s["key"] == "wg_gesucht")
    assert wg_source["enabled"] is False
    assert wg_source["unavailable_reason"]


def test_cannot_enable_unavailable_source(db_session):
    run_seed(db_session)
    resp = client.patch("/api/sources/wg_gesucht", json={"enabled": True})
    assert resp.status_code == 400


def test_seed_then_list_search_profiles(db_session):
    run_seed(db_session)
    resp = client.get("/api/search-profiles")
    assert resp.status_code == 200
    data = resp.json()
    names = {p["name"] for p in data}
    assert "Hannover Studio October" in names
    assert "Hannover Ultra Budget" in names


def test_manual_search_run_populates_listings(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    run_seed(db_session)

    resp = client.post("/api/search/run")
    assert resp.status_code == 200
    run_data = resp.json()
    assert run_data["total_discovered"] == 4
    assert run_data["trigger"] == "manual"

    listings_resp = client.get("/api/listings")
    assert listings_resp.status_code == 200
    listings_data = listings_resp.json()
    assert listings_data["total"] == 4
    get_settings.cache_clear()


def test_dashboard_stats_endpoint(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    run_seed(db_session)
    client.post("/api/search/run")

    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["sources_total"] >= 1
    assert "high_priority" in stats
    get_settings.cache_clear()


def test_export_csv(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    run_seed(db_session)
    client.post("/api/search/run")

    resp = client.get("/api/listings/export/csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "title" in resp.text
    get_settings.cache_clear()


def test_run_history_records_run(db_session, monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("EMAIL_NOTIFICATIONS_ENABLED", "false")
    monkeypatch.setenv("TELEGRAM_NOTIFICATIONS_ENABLED", "false")
    run_seed(db_session)
    client.post("/api/search/run")

    resp = client.get("/api/run-history")
    assert resp.status_code == 200
    runs = resp.json()
    assert len(runs) >= 1
    assert runs[0]["trigger"] == "manual"
    get_settings.cache_clear()
