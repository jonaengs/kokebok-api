from typing import Protocol

from ninja import ModelSchema
from recipes.models import RecipeIngredient


class ScrapedRecipeIngredient(ModelSchema):
    base_ingredient_str: str

    class Config:
        model = RecipeIngredient
        model_exclude = ["base_ingredient", "recipe"]


IngredientGroupDict = dict[str, list[ScrapedRecipeIngredient]]


HTML = str


class MyScraper(Protocol):
    def ingredient_groups(
        self,
    ) -> dict[str, list[ScrapedRecipeIngredient]]:
        raise NotImplementedError()

    def preamble(self) -> str:
        raise NotImplementedError()

    def content(self) -> HTML:
        raise NotImplementedError()
