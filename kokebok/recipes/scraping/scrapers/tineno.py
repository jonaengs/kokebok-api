import copy
import json
import re
from collections import defaultdict

import extruct
import requests
from bs4 import BeautifulSoup, Tag
from recipe_scrapers.tineno import TineNo
from recipes.scraping.base import (
    HTML,
    IngredientGroupDict,
    MyScraper,
    ScrapedRecipeIngredient,
)
from w3lib.html import get_base_url

# Tests TODO:
# * Check that no methods modify the raw html, json_ld_data or soup objects
# * Check that no methods crash & that results are returned as expected
# * Check that it conforms to the expected interface (wrt methods and return types)
# * Check that methods which return HTML content return safe HTML


class TineNoScraper(TineNo, MyScraper):
    def __init__(self, url: str, html: str | None = None) -> None:
        # We basically parse the page three times because
        # recipe_scrapers doesn't give enough information
        self.page_raw = html or requests.get(url).content.decode("utf-8")
        self.json_ld_data = extruct.extract(
            self.page_raw,
            syntaxes=["json-ld"],
            base_url=get_base_url(self.page_raw, url),
        )["json-ld"][0]
        self.page_soup = BeautifulSoup(self.page_raw, "html.parser")

        super(TineNoScraper, self).__init__(url, html=self.page_raw)

    def ingredient_groups(self) -> IngredientGroupDict:
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
            group_name = group["name"] or ""  # Use empty string as key if name=None
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
                    base_ingredient_str=ingr["ingredient"]["genericName"],
                    amount=ingr["amount"],
                    unit=ingr["unit"]["singular"],
                    is_optional=ingr["omissible"],
                    group_name=group_name,
                )
                result[group_name].append(data)

        return result

    def ingress(self) -> str:
        return self.json_ld_data["description"]

    def content(self) -> HTML:
        def strip_attrs(tag: Tag):
            attrs = list(tag.attrs.keys())
            for key in attrs:
                del tag[key]

        # Extract the tip section
        found = self.page_soup.find_all(attrs={"class": "m-tip"})
        # Expect a single div
        assert len(found) <= 1, found
        # Copy tag before removing attributes
        tip_div: Tag = copy.copy(found[0])
        # Strip attributes off the div and its children
        strip_attrs(tip_div)
        for child in tip_div.descendants:
            if isinstance(child, Tag):
                strip_attrs(child)
            # print(type(child), child.name)
            # if child.name:  # Use name attribute as a proxy for determining a tag
        # Fix fucky indentation
        formatted = tip_div.prettify(formatter="html")
        return formatted
