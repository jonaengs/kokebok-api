from typing import Protocol

from ninja import ModelSchema
from recipes.models import RecipeIngredient


class ScrapedRecipeIngredient(ModelSchema):
    base_ingredient_str: str

    class Config:
        model = RecipeIngredient
        model_exclude = ["base_ingredient", "recipe"]


HTML = str


class MyScraper(Protocol):
    def ingredient_groups(
        self,
    ) -> dict[str, list[ScrapedRecipeIngredient]]:
        ...

    def ingress(self) -> str:
        ...

    def content(self) -> HTML:
        ...
