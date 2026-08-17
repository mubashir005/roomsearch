"""Central registry mapping source keys to adapter classes.

To add a new source: write an AccommodationSource subclass anywhere under
app/sources/, import it here, and add it to SOURCE_REGISTRY. Nothing else
in the application (scheduler, API, dashboard) needs to change.
"""
from __future__ import annotations

from app.sources.base import AccommodationSource
from app.sources.housinganywhere import HousingAnywhereSource
from app.sources.immonet import ImmonetSource
from app.sources.immoscout24 import ImmoScout24Source
from app.sources.immowelt import ImmoweltSource
from app.sources.kleinanzeigen import KleinanzeigenSource
from app.sources.meinestadt import MeinestadtSource
from app.sources.mock_demo import MockDemoSource
from app.sources.rss_generic import GenericRssSource
from app.sources.wg_gesucht import WgGesuchtSource
from app.sources.wunderflats import WunderflatsSource

SOURCE_REGISTRY: dict[str, type[AccommodationSource]] = {
    "mock_demo": MockDemoSource,
    "rss_generic": GenericRssSource,
    "meinestadt": MeinestadtSource,
    "wg_gesucht": WgGesuchtSource,
    "kleinanzeigen": KleinanzeigenSource,
    "immoscout24": ImmoScout24Source,
    "immowelt": ImmoweltSource,
    "immonet": ImmonetSource,
    "housinganywhere": HousingAnywhereSource,
    "wunderflats": WunderflatsSource,
}


def get_source_class(key: str) -> type[AccommodationSource] | None:
    return SOURCE_REGISTRY.get(key)


def instantiate(key: str, config: dict | None = None) -> AccommodationSource | None:
    cls = get_source_class(key)
    if cls is None:
        return None
    return cls(config=config)
