"""Immowelt adapter -- DISABLED.

Reason: Immowelt's ToS prohibits automated data extraction and offers no
public search API or RSS feed for individual/non-commercial use. Disabled
per the project's legal rules.

To enable: obtain an official data feed/API agreement with Immowelt (they
offer commercial listing-syndication products) and implement against it.
"""
from __future__ import annotations

from app.sources.disabled import DisabledSource


class ImmoweltSource(DisabledSource):
    key = "immowelt"
    display_name = "Immowelt"
    unavailable_reason = (
        "Immowelt ToS prohibits automated scraping and has no public API/RSS. Disabled pending "
        "an official data-feed agreement."
    )
