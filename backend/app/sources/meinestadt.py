"""Meinestadt.de adapter -- DISABLED BY DEFAULT.

Meinestadt classifieds have historically exposed RSS feeds for some search
categories, which would make this a legitimate, ToS-friendly source. This
adapter is implemented as a thin wrapper around GenericRssSource so it can
be enabled the moment a working Hannover-accommodation feed URL is
confirmed -- it is left disabled by default because no feed URL has been
verified as part of this build (verifying requires checking meinestadt.de's
current robots.txt and feed availability, which the operator should do
before enabling).
"""
from __future__ import annotations

from app.sources.rss_generic import GenericRssSource


class MeinestadtSource(GenericRssSource):
    key = "meinestadt"
    display_name = "Meinestadt"
    # Inherits GenericRssSource.available = True, but the Source DB row is
    # seeded with enabled=False and no feed_url until one is configured.
