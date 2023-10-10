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

    class Config:
        model = RecipeIngredient
        model_exclude = ["base_ingredient", "recipe"]

    def clean(self):
        ...


IngredientGroupDict = dict[str, list[ScrapedRecipeIngredient]]


class ScrapedRecipe(ModelSchema):
    hero_image_link: str
    ingredients: IngredientGroupDict

    class Config:
        model = Recipe
        model_exclude = ["hero_image", "created_at", "video_url", "other_source"]

    def clean(self):
        if self.language and self.language not in Recipe.Languages.choices:
            raise ValidationError(f"Illegal language: {self.language}")
        for group_name, ingredients in self.ingredients.items():
            if not all(ingr.group_name == group_name for ingr in ingredients):
                raise ValidationError("Group names must all be the same")
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
