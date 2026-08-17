"""Wunderflats adapter -- DISABLED.

Reason: Wunderflats' ToS prohibits automated scraping and it offers no
public search API/RSS for individual users. Disabled per the project's
legal rules.

To enable: obtain official API access from Wunderflats and implement
against it.
"""
from __future__ import annotations

from app.sources.disabled import DisabledSource


class WunderflatsSource(DisabledSource):
    key = "wunderflats"
    display_name = "Wunderflats"
    unavailable_reason = (
        "Wunderflats ToS prohibits automated scraping and offers no public search API. "
        "Disabled pending official API access."
    )
