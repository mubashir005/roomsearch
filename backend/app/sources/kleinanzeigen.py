"""Kleinanzeigen (formerly eBay Kleinanzeigen) adapter -- DISABLED.

Reason: Kleinanzeigen's ToS forbids automated access/scraping and the site
uses active bot-detection (e.g. rate-based blocking, JS challenges). eBay
Kleinanzeigen shut down its public listings API for third parties. No RSS
feed is offered for search results. Disabled per the project's legal rules.

To enable: obtain official API access (Kleinanzeigen occasionally offers
partner APIs for commercial use cases) and implement against it.
"""
from __future__ import annotations

from app.sources.disabled import DisabledSource


class KleinanzeigenSource(DisabledSource):
    key = "kleinanzeigen"
    display_name = "Kleinanzeigen"
    unavailable_reason = (
        "Kleinanzeigen ToS prohibits automated scraping, uses bot-detection, and has no public "
        "listings API. Disabled pending official API access."
    )
