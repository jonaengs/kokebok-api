import functools
from typing import Protocol

from django.forms import ValidationError
from ninja import ModelSchema
from recipe_scrapers._abstract import AbstractScraper

from recipes.models import Recipe, RecipeIngredient

# TODO: Make sure all keys in this dict are members of RecipeIngrediet.Units
_UNITS = {
    # Weight
    "g": ("gram", "grams"),
    "kg": ("kilo", "kilos", "kilogram", "kilograms"),
    "oz": ("ounce", "ounces"),
    "lb": ("pound", "pounds"),
    # Volume
    "cup": ("cup", "cups"),
    "tbsp": ("tablespoon", "tablespoons", "ss"),
    "tsp": ("teaspoon", "teaspoons", "ts"),
    "dl": ("decilitre", "decilitres", "desiliter"),
    # Other
    "count": ("", "stk", "stk."),
    "slice": ("slice", "slices"),
    "inch": ("inches", "″"),
    "cm": ("centimetre", "centimetres"),
    # TODO: Fill
}

UNIT_STRINGS: dict[str, str] = functools.reduce(
    lambda acc, kv: acc | {v: kv[0] for v in kv[1]} | {kv[0]: kv[0]},
    _UNITS.items(),
    {},
)


class ScrapedRecipeIngredient(ModelSchema):
    base_ingredient_str: str = ""

    class Meta:
        model = RecipeIngredient
        exclude = ["base_ingredient", "recipe", "id"]

    def clean(self):
        ...


IngredientGroupDict = dict[str, list[ScrapedRecipeIngredient]]


class ScrapedRecipe(ModelSchema):
    hero_image_link: str | None = None
    ingredients: IngredientGroupDict

    class Meta:
        model = Recipe
        exclude = [
            "id",
            "hero_image",
            "created_at",
            "video_url",
            "other_source",
        ]

    # error if given kwargs not in the schema
    model_config = {"extra": "forbid"}

    def clean(self):
        """Note: Will try modifying the language if it's not a valid language code."""
        if self.language and self.language not in Recipe.Languages.codes():
            entire_lang_string = self.language.lower()
            # handle cases like "en-US", "nb-NO"
            if "-" in self.language:
                parts = entire_lang_string.split("-")
                for part in parts:
                    if part in Recipe.Languages.codes():
                        self.language = part
                        return self.clean()
            raise ValidationError(
                f"Illegal language: {self.language} (entire={entire_lang_string})"
            )
        for group_name, ingredients in self.ingredients.items():
            for ingr in ingredients:
                ingr.clean()


HTML = str


class MyScraperProtocol(Protocol):
    def __init__(self, *args, **kwargs):
        super(MyScraperProtocol, self).__init__(self, *args, **kwargs)

    def my_ingredient_groups(
        self,
    ) -> dict[str, list[ScrapedRecipeIngredient]]:
        ...

    def my_preamble(self) -> str:
        ...

    def my_content(self) -> HTML:
        ...


# Protocol for classes implementing MyScraper.
# Until we get typing intersections with the '&' operator, this will have to do.
class MyScraper(MyScraperProtocol, AbstractScraper):
    ...
