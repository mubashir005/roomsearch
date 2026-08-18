import asyncio
import json

from app.ai_parsing import parse_listing_with_ai
from app.config import get_settings


def test_ai_parsing_disabled_without_key(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "")
    result = asyncio.run(parse_listing_with_ai("1 Zimmer Wohnung, 480 Warmmiete"))
    assert result is None
    get_settings.cache_clear()


def test_ai_parsing_empty_text_returns_none(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    result = asyncio.run(parse_listing_with_ai("   "))
    assert result is None
    get_settings.cache_clear()


def test_ai_parsing_success(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": json.dumps({"rooms": 1, "rent_warm": 480})}}]}

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

    result = asyncio.run(parse_listing_with_ai("1 room apartment for 480 warm"))
    assert result == {"rooms": 1, "rent_warm": 480}
    get_settings.cache_clear()


def test_ai_parsing_handles_failure_gracefully_no_raise(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FailingAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, *a, **kw):
            raise ConnectionError("network down")

    import app.ai_parsing as ai_parsing_module

    monkeypatch.setattr(ai_parsing_module.httpx, "AsyncClient", FailingAsyncClient)

    result = asyncio.run(parse_listing_with_ai("some text"))
    assert result is None
    get_settings.cache_clear()
