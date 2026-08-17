"""WG-Gesucht.de adapter -- DISABLED.

Reason: WG-Gesucht's Terms of Service (Nutzungsbedingungen) prohibit
automated retrieval/scraping of listing data, and the site has no public
search API or RSS feed for individuals. Their pages are also protected by
bot-detection. Per the project's legal rules (no ToS bypass, no anti-bot
evasion), this adapter is implemented as an interface stub only.

To enable: obtain a written data-partnership/API agreement with WG-Gesucht,
then implement `search`/`get_listing` against that official API and flip
`available = True`.
"""
from __future__ import annotations

from app.sources.disabled import DisabledSource


class WgGesuchtSource(DisabledSource):
    key = "wg_gesucht"
    display_name = "WG-Gesucht"
    unavailable_reason = (
        "WG-Gesucht ToS prohibits automated scraping and offers no public API/RSS feed. "
        "Disabled pending an official data partnership."
    )
