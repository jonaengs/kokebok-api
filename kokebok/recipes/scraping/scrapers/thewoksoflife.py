import re
from collections import defaultdict
from copy import deepcopy

import bs4
import extruct
import requests
from bs4 import BeautifulSoup
from recipe_scrapers.thewoksoflife import Thewoksoflife

from recipes.scraping.base import (
    HTML,
    UNIT_STRINGS,
    IngredientGroupDict,
    MyScraperProtocol,
    ScrapedRecipeIngredient,
)
from recipes.scraping.utils import recursive_strip_attrs

# NOTE: The base Thewoksoflife class does not support the description method.
# We could probably make a PR using the preamble code


class TheWoksOfLifeScraper(MyScraperProtocol, Thewoksoflife):
    def __init__(self, url: str | None, html: str | None = None) -> None:
        # We basically parse the page three times because
        # recipe_scrapers doesn't give enough information
        self.page_raw = html or requests.get(url).content.decode("utf-8")  # type: ignore[arg-type] # noqa
        self.page_soup = BeautifulSoup(self.page_raw, "html.parser")

        json_ld_extract = extruct.extract(self.page_raw, syntaxes=["json-ld"])
        self.json_ld_data = json_ld_extract["json-ld"][0]

        super().__init__(url, html=self.page_raw)

    def my_ingredient_groups(self) -> IngredientGroupDict:
        group_containers = self.page_soup.find_all(
            attrs={"class": "wprm-recipe-ingredient-group"},
        )
        result: IngredientGroupDict = defaultdict(list)
        for group in group_containers:
            group_name = group.h4.text.strip() if group.h4 else ""

            for li in group.ul:
                ingredient_name = li.find(
                    attrs={"class": "wprm-recipe-ingredient-name"}
                ).text.strip()

                # Extract the note, and encase it in parens if it isn't already
                notes_li = li.find(attrs={"class": "wprm-recipe-ingredient-notes"})
                if notes_li:
                    ingredient_note = notes_li.text.strip()
                    if not (ingredient_note[0] == "(" and ingredient_note[-1] == ")"):
                        ingredient_note = f"({ingredient_note})"
                    ingredient_note = " " + ingredient_note
                else:
                    ingredient_note = ""
                ingredient_long_name = ingredient_name + ingredient_note

                # Try to get unit and convert it to accepted format
                unit_li = li.find(attrs={"class": "wprm-recipe-ingredient-unit"})
                unit = unit_li.text if unit_li else ""
                if unit_li and unit not in UNIT_STRINGS:
                    # If we don't know the unit, append it to the long name
                    ingredient_long_name = unit + " " + ingredient_long_name
                    unit = ""
                else:
                    unit = UNIT_STRINGS[unit]

                # Amount examples: "1", "13.5", "3/4", "1 1/2", "10-12"
                amount_li = li.find(attrs={"class": "wprm-recipe-ingredient-amount"})
                if amount_li:
                    # Make sure we aren't calling eval on anything scary
                    if re.match(r"[ \d\/\.]*\Z", amount_li.text):
                        amount = sum(eval(s) for s in amount_li.text.split(" "))
                    else:
                        # Unable to parse amount.
                        # Make amount and unit blank, and put them in the long name
                        amount = 0
                        ingredient_long_name = li.text[2:]
                        unit = ""
                else:
                    amount = 0

                data = ScrapedRecipeIngredient(
                    name_in_recipe=ingredient_long_name,
                    base_ingredient_str=ingredient_name,
                    base_amount=amount,
                    unit=unit,
                    is_optional="optional" in ingredient_note,
                    group_name=group_name,
                )
                result[group_name].append(data)

        return dict(result)

    def my_preamble(self) -> str:
        nodes: list[dict] = self.json_ld_data["@graph"]
        for node in nodes:
            if node["@id"].endswith("/#recipe"):
                return node["description"]
        return ""

    def my_content(self) -> HTML:
        tips_div = self.page_soup.find(attrs={"class": "wprm-recipe-notes-container"})
        if tips_div:
            # Don't handle bs4.NavigableString
            assert isinstance(tips_div, bs4.Tag), tips_div
            tips_div = deepcopy(tips_div)
            recursive_strip_attrs(tips_div, None)

        # Select text and images from the article
        article_tags = self.page_soup.select(
            "article > div > p, article > div > figure"
        )
        article_contents = [
            recursive_strip_attrs(deepcopy(tag), attrs=["class", "id"])
            for tag in article_tags
        ]

        return (
            "<div>\n"
            + (f"{tips_div}\n\n" if tips_div else "")
            + "\n".join(map(str, article_contents))
            + "\n</div>"
        )
