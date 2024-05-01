import json
import re
from collections import defaultdict
from functools import lru_cache

import extruct
import requests
from bs4 import BeautifulSoup
from recipe_scrapers.tineno import TineNo

from recipes.scraping.base import (
    HTML,
    IngredientGroupDict,
    MyScraperProtocol,
    ScrapedRecipeIngredient,
)
from recipes.scraping.utils import html_to_markdown


class TineNoScraper(MyScraperProtocol, TineNo):
    def __init__(self, url: str | None, html: str | None = None) -> None:
        assert url or html, "Either url or html must be provided"
        self.page_raw = html or requests.get(url).content.decode("utf-8")  # type: ignore[arg-type] # if not html, url must be string
        self.page_soup = BeautifulSoup(self.page_raw, "html.parser")

        json_ld_extract = extruct.extract(self.page_raw, syntaxes=["json-ld"])
        self.json_ld_data = json_ld_extract["json-ld"][0]

        super().__init__(url, html=self.page_raw)

    def my_ingredient_groups(self) -> IngredientGroupDict:
        def tine_remove_links(match: re.Match) -> str:
            """Returns the contents of an anchor tag"""
            soup = BeautifulSoup(match.string, "html.parser")
            return soup.text

        # All ingredient data can be found within a data-json container,
        # grouped by their group name
        found = self.page_soup.find_all(attrs={"data-json": True})
        assert len(found) == 1, found
        ingredients_data = json.loads(found[0]["data-json"])

        result: IngredientGroupDict = defaultdict(list)
        for group in ingredients_data:
            # Clean up the ingredient group name
            group_name = group["name"] or ""  # Use empty string as key if name=None
            group_name = group_name.strip()
            if group_name.endswith(":"):
                group_name = group_name[:-1]

            for ingr in group["ingredientLines"]:
                # Retrieving the ingredient name requires a little work
                content = ingr["content"]
                name = (
                    content["infoBefore"]
                    + content["ingredientContent"]
                    + content["infoAfter"]
                )
                name = re.sub(r"<a [^<]+<\/a>", tine_remove_links, string=name)

                data = ScrapedRecipeIngredient(
                    name_in_recipe=name,
                    base_ingredient_str=(
                        ingr["ingredient"]["genericName"]
                        or ingr["ingredient"]["singular"]
                        or ingr["content"]["ingredientContent"]
                    ),
                    base_amount=ingr["amount"],
                    unit=ingr["unit"]["singular"],
                    is_optional=ingr["omissible"],
                    group_name=group_name,
                )
                result[group_name].append(data)

        return dict(result)

    def my_preamble(self) -> str:
        return self.json_ld_data["description"]

    @lru_cache(maxsize=1)  # expensive call so we cache it. Mostly relevant for testing
    def my_content(self) -> HTML:
        # Extract the tip section divs
        # First class is for end-of-article tips, second is for instruction tips
        tip_tags = self.page_soup.find_all(
            attrs={"class": ["m-tip", "o-recipe-steps--group__list__tip"]}
        )
        return "\n\n".join(html_to_markdown(str(tag)) for tag in tip_tags)
