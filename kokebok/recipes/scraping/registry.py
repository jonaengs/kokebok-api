from recipes.scraping.base import MyScraper
from recipes.scraping.scrapers.thewoksoflife import TheWoksOfLifeScraper
from recipes.scraping.scrapers.tineno import TineNoScraper

# If Mypy emits [type-abstract] errors here, it's likely due to a class missing
# one or more methods required by the MyScraperProtocol

"""
Registry of custom recipe site scrapers.
If you add another scraper it must be registered here to get used
for scraping.
"""
registry: dict[str, type[MyScraper]] = {
    #
    TineNoScraper.host(): TineNoScraper,
    TheWoksOfLifeScraper.host(): TheWoksOfLifeScraper,
}
