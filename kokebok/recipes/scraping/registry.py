from recipe_scrapers._abstract import AbstractScraper
from recipes.scraping.base import MyScraperProtocol
from recipes.scraping.scrapers.thewoksoflife import TheWoksOfLifeScraper
from recipes.scraping.scrapers.tineno import TineNoScraper


# Protocol for classes implementing MyScraper.
# Until we get typing intersections with the '&' operator, this will have to do.
class MyScraper(MyScraperProtocol, AbstractScraper):
    ...


# If Mypy emits [type-abstract] errors here, it's likely due to a class missing
# one or more methods required by the MyScraperProtocol
_registry: dict[str, type[MyScraper]] = {
    #
    TineNoScraper.host(): TineNoScraper,
    TheWoksOfLifeScraper.host(): TheWoksOfLifeScraper,
}
