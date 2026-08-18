"""Optional AI parsing fallback (task section 29).

Deterministic parsing (matching/price_parser.py, matching/german_terms.py)
is always tried first and is sufficient for every source this build ships.
This module exists for messy free-form text -- e.g. a listing description a
user pastes in via "Quick Add" -- where deterministic regexes may leave
several fields unknown. It is never required: with no OPENAI_API_KEY set,
callers simply get back an empty result and keep whatever deterministic
parsing already found.
"""
from __future__ import annotations

import json
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You extract structured apartment-listing data from German or English free text. "
    "Only report a field if the text actually states or clearly implies it -- leave a field "
    "null rather than guessing. Never invent a value. Distinguish Kaltmiete (cold rent) from "
    "Warmmiete (warm/total rent) carefully; if only cold rent plus Nebenkosten/Heizkosten are "
    "given, compute warm rent as their sum and set rent_warm_is_estimated to true. If no rent "
    "figure can be determined at all, leave rent_warm null."
)

_JSON_SCHEMA = {
    "name": "listing_fields",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": ["string", "null"]},
            "address": {"type": ["string", "null"]},
            "district": {"type": ["string", "null"]},
            "city": {"type": ["string", "null"]},
            "postcode": {"type": ["string", "null"]},
            "rent_cold": {"type": ["number", "null"]},
            "rent_warm": {"type": ["number", "null"]},
            "rent_warm_is_estimated": {"type": ["boolean", "null"]},
            "utilities": {"type": ["number", "null"]},
            "heating_cost": {"type": ["number", "null"]},
            "size_sqm": {"type": ["number", "null"]},
            "rooms": {"type": ["number", "null"]},
            "furnished": {
                "type": ["string", "null"],
                "enum": ["furnished", "partially_furnished", "unfurnished", "unknown", None],
            },
            "private_bathroom": {"type": ["boolean", "null"]},
            "private_kitchen": {"type": ["boolean", "null"]},
            "balcony": {"type": ["boolean", "null"]},
            "anmeldung": {
                "type": ["string", "null"],
                "enum": ["possible", "impossible", "unknown", None],
            },
            "rental_type": {
                "type": ["string", "null"],
                "enum": ["long_term", "temporary", "zwischenmiete", "unknown", None],
            },
            "availability_date": {"type": ["string", "null"], "description": "ISO 8601 date, e.g. 2026-10-01"},
        },
        "required": [
            "title", "address", "district", "city", "postcode", "rent_cold", "rent_warm",
            "rent_warm_is_estimated", "utilities", "heating_cost", "size_sqm", "rooms",
            "furnished", "private_bathroom", "private_kitchen", "balcony", "anmeldung",
            "rental_type", "availability_date",
        ],
    },
}


async def parse_listing_with_ai(text: str) -> dict | None:
    """Returns a dict of extracted fields (any of which may be None), or
    None if AI parsing is disabled/unavailable/failed. Never raises."""
    settings = get_settings()
    if not settings.OPENAI_API_KEY or not text.strip():
        return None

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text[:6000]},
        ],
        "response_format": {"type": "json_schema", "json_schema": _JSON_SCHEMA},
        "temperature": 0,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:  # noqa: BLE001 -- AI parsing is a best-effort fallback, never fatal
        logger.exception("AI parsing fallback failed; continuing with deterministic fields only")
        return None
