"""Immonet adapter -- DISABLED.

Reason: Immonet is now operated by the same group as Immowelt and shares its
listing inventory; it has the same ToS restrictions against automated
scraping and no public API/RSS feed for individual use. Disabled per the
project's legal rules.

To enable: same path as Immowelt -- an official data-feed/API agreement.
"""
from __future__ import annotations

from app.sources.disabled import DisabledSource


class ImmonetSource(DisabledSource):
    key = "immonet"
    display_name = "Immonet"
    unavailable_reason = (
        "Immonet ToS prohibits automated scraping and has no public API/RSS. Disabled pending "
        "an official data-feed agreement."
    )
