import json
import re
from collections import defaultdict
from typing import Any

import bs4
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

# Tests TODO:
# * Check that methods which return HTML content return safe HTML?

# TODO: Consider changing parser to lxml for improved performance


class TineNoScraper(MyScraperProtocol, TineNo):
    def __init__(self, url: str | None, html: str | None = None) -> None:
        # We basically parse the page three times because
        # recipe_scrapers doesn't give enough information
        self.page_raw = html or requests.get(url).content.decode("utf-8")  # type: ignore[arg-type] # noqa
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

        # pprint(ingredients_data)

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

    def my_content(self) -> HTML:
        def extract_tips(tags: bs4.ResultSet[Any]):
            contents = "".join(
                "\n\n" + tag.text.replace("Tips", "").strip() for tag in tags
            )
            html_str = f"<div><h4>Tips</h4>{contents}</div>"
            return html_str

        # Extract the tip section divs
        # First class is for end-of-article tips, second is for instruction tips
        tip_tags = self.page_soup.find_all(
            attrs={"class": ["m-tip", "o-recipe-steps--group__list__tip"]}
        )

        # Prettify html string, then strip indentation
        formatted = BeautifulSoup(
            extract_tips(tip_tags), "html.parser", preserve_whitespace_tags=["h4"]
        ).prettify()
        formatted = "\n".join(line.strip() for line in formatted.split("\n"))
        return formatted
