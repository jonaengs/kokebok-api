from typing import NamedTuple

import recipe_scrapers
from recipe_scrapers import scrape_html, scrape_me
from recipe_scrapers._abstract import AbstractScraper
from recipe_scrapers._utils import get_host_name

from recipes.scraping.base import (
    UNIT_STRINGS,
    MyScraper,
    ScrapedRecipe,
    ScrapedRecipeIngredient,
)
from recipes.scraping.registry import _registry
from recipes.scraping.utils import RecipeScraperWrapper


def parse_ingredient_string(
    s: str, group: str | None = None
) -> ScrapedRecipeIngredient:
    """
    Tries matching the ingredient string against:
    "<amt> <unit> <ingredient_name>"
    """
    for i, c in enumerate(s):
        if not c.isdigit():
            break

    amount = float(s[:i] or 0)
    maybe_measure = s[i:].strip().split()[0]
    measure = UNIT_STRINGS.get(maybe_measure, "count") if amount else ""

    if measure:
        ingredient_name = s[s.find(maybe_measure) + len(maybe_measure) :].strip()
    elif amount:
        ingredient_name = s[i:].strip()
    else:
        ingredient_name = ""

    return ScrapedRecipeIngredient(
        name_in_recipe=s,
        base_ingredient_str=ingredient_name,
        base_amount=amount,
        unit=measure,
        group_name=group,
    )


def scrape(
    url: str | None, html: str | None = None, host: str | None = None
) -> ScrapedRecipe:
    """html & host params are for testing against local files"""
    (in_my_registry, _, scraper) = get_scraper(url, html, host)
    wrapped = RecipeScraperWrapper(scraper)

    # Get ingredient groups
    if in_my_registry:
        scraped_ingredients = scraper.my_ingredient_groups()
    else:
        wrapped
        try:
            groups = wrapped.ingredient_groups()
            scraped_ingredients = {
                group: [
                    parse_ingredient_string(ingredient, group)
                    for ingredient in group.ingredients
                ]
                for group in groups
            }
        except:  # noqa
            scraped_ingredients = {
                "": [
                    parse_ingredient_string(ingredient)
                    for ingredient in wrapped.ingredients() or []
                ]
            }

    # Preprocess instructions a little
    instructions = scraper.instructions_list()
    instructions = "\n\n".join(
        f"{i}. {instr}" for i, instr in enumerate(instructions, 1)
    )
    instructions = instructions or None

    return ScrapedRecipe(
        title=wrapped.title() or "",
        instructions=instructions,
        original_author=wrapped.author() or "",
        language=wrapped.language() or "",
        preamble=scraper.my_preamble()
        if in_my_registry
        else (wrapped.description() or ""),
        rest_text=scraper.my_content()
        if in_my_registry
        else (wrapped.all_text() or ""),
        origin_url=url,
        total_time=wrapped.total_time(),
        # yields_number=wrapped.yields(),
        hero_image_link=wrapped.image(),
        ingredients=scraped_ingredients,
    )


class RegistryLookupResult(NamedTuple):
    host_in_my_registry: bool
    host_in_scrapers_registry: bool  # recipe scrapers has its own "registry" of supported sites
    scraper: AbstractScraper | MyScraper


# TODO: Redesign this interface
def get_scraper(url: str | None, html=None, host=None) -> RegistryLookupResult:
    host = host or (get_host_name(url) if url else "")
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
        scraper=scrape_html(html, url, wild_mode=True)
        if html
        else scrape_me(url, wild_mode=True),
    )
