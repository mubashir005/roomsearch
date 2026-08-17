"""ImmoScout24 adapter -- DISABLED.

Reason: ImmoScout24 provides an official Partner API, but it requires a
commercial partnership/contract and API key issued by ImmoScout24 -- it is
not a free/public API an individual user can self-serve. Scraping the public
site is explicitly forbidden by their ToS and protected by bot-detection
(reCAPTCHA-class challenges). Disabled per the project's legal rules.

To enable: sign up for the ImmoScout24 Partner API, put the issued
credentials in .env, and implement `search`/`get_listing` against that API.
"""
from __future__ import annotations

from app.sources.disabled import DisabledSource


class ImmoScout24Source(DisabledSource):
    key = "immoscout24"
    display_name = "ImmoScout24"
    unavailable_reason = (
        "ImmoScout24 only offers a commercial Partner API (contract required); public scraping is "
        "forbidden by ToS and bot-protected. Disabled pending Partner API credentials."
    )
