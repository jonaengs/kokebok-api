from typing import NamedTuple

import recipe_scrapers
from recipe_scrapers import scrape_html, scrape_me
from recipe_scrapers._abstract import AbstractScraper
from recipe_scrapers._utils import get_host_name
from recipes.scraping.base import MyScraper
from recipes.scraping.registry import _registry


# Protocol for classes implementing MyScraper.
# Until we get typing intersections with the '&' operator, this will have to do.
class MyScraperProtocol(AbstractScraper, MyScraper):
    ...


class RegistryLookupResult(NamedTuple):
    host_in_my_registry: bool
    host_in_scrapers_registry: bool
    scraper: AbstractScraper | MyScraperProtocol


def get_scraper(url, html=None) -> RegistryLookupResult:
    host = get_host_name(url)
    if host in _registry:
        return RegistryLookupResult(
            host_in_my_registry=True,
            host_in_scrapers_registry=True,
            scraper=_registry[host](url, html),
        )
    elif host in recipe_scrapers.SCRAPERS:
        return RegistryLookupResult(
            host_in_my_registry=False,
            host_in_scrapers_registry=True,
            scraper=scrape_html(html, url) if html else scrape_me(url),
        )
    return RegistryLookupResult(
        host_in_my_registry=False,
        host_in_scrapers_registry=False,
        scraper=recipe_scrapers.scrape_me(url, wild_mode=True),
    )
