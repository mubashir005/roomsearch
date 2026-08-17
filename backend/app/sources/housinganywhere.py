"""HousingAnywhere adapter -- DISABLED.

Reason: HousingAnywhere's ToS prohibits automated scraping of listings and
there is no free public search API for individual users (they offer
landlord/property-manager integrations, not search-result feeds). Disabled
per the project's legal rules.

To enable: obtain official API access from HousingAnywhere and implement
against it.
"""
from __future__ import annotations

from app.sources.disabled import DisabledSource


class HousingAnywhereSource(DisabledSource):
    key = "housinganywhere"
    display_name = "HousingAnywhere"
    unavailable_reason = (
        "HousingAnywhere ToS prohibits automated scraping and offers no public search API. "
        "Disabled pending official API access."
    )
