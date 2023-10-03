from typing import NamedTuple

import recipe_scrapers
from recipe_scrapers._abstract import AbstractScraper
from recipe_scrapers._utils import get_host_name
from recipes.scraping.base import MyScraper
from recipes.scraping.registry import _registry


class RegistryLookupResult(NamedTuple):
    host_in_my_registry: bool
    host_in_scrapers_registry: bool
    scraper: AbstractScraper | MyScraper


def get_scraper(url) -> RegistryLookupResult:
    host = get_host_name(url)
    if host in _registry:
        return RegistryLookupResult(
            host_in_my_registry=True,
            host_in_scrapers_registry=True,
            scraper=_registry[host](url),
        )
    elif host in recipe_scrapers.SCRAPERS:
        return RegistryLookupResult(
            host_in_my_registry=False,
            host_in_scrapers_registry=True,
            scraper=recipe_scrapers.scrape_me(url),
        )
    return RegistryLookupResult(
        host_in_my_registry=False,
        host_in_scrapers_registry=False,
        scraper=recipe_scrapers.scrape_me(url, wild_mode=True),
    )
