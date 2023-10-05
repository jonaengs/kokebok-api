import functools
from typing import Protocol

from ninja import ModelSchema
from recipes.models import RecipeIngredient

# TODO: Make sure all keys in this dict are members of RecipeIngrediet.Units
_UNITS = {
    # Weight
    "g": ("gram", "grams"),
    "kg": ("kilo", "kilos", "kilogram", "kilograms"),
    "oz": ("ounce", "ounces"),
    "lb": ("pound", "pounds"),
    # Volume
    "cup": ("cup", "cups"),
    "tbsp": ("tablespoon", "tablespoons"),
    "tsp": ("teaspoon", "teaspoons"),
    # Other
    "count": ("",),
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
    base_ingredient_str: str | None

    class Config:
        model = RecipeIngredient
        model_exclude = ["base_ingredient", "recipe"]


IngredientGroupDict = dict[str, list[ScrapedRecipeIngredient]]


HTML = str


class MyScraperProtocol(Protocol):
    def __init__(self, url: str | None, html: str | None):
        ...

    def ingredient_groups(
        self,
    ) -> dict[str, list[ScrapedRecipeIngredient]]:
        ...

    def preamble(self) -> str:
        ...

    def content(self) -> HTML:
        ...
