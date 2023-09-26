from itertools import groupby

from django.urls import path
from ninja import Field, ModelSchema, NinjaAPI, Schema
from recipes.models import Ingredient, Recipe, RecipeIngredient

api = NinjaAPI()


class ModelRecipeSchema(ModelSchema):
    class Config:
        model = Recipe
        model_fields = "__all__"  # TODO: don't use __all__


class ModelIngredientSchema(ModelSchema):
    names: list[str | None]

    class Config:
        model = Ingredient
        model_fields = ["id", "is_ubiquitous"]

    @staticmethod
    def resolve_names(obj):
        return obj.get_names()


class ModelRecipeIngredientSchema(ModelSchema):
    class Config:
        model = RecipeIngredient
        model_fields = "__all__"  # TODO: don't use __all__


class RecipeIngredientSchema(Schema):
    id: int
    name: str = Field(alias="name_in_recipe")
    is_optional: bool
    ingredient_id: int = Field(alias="base_ingredient_id")


class RecipeSchema(Schema):
    recipe: ModelRecipeSchema
    ingredients: list[RecipeIngredientSchema]


@api.get("/recipes", response=list[ModelRecipeSchema])
def list_recipes(_request):
    return Recipe.objects.all()


@api.get("/ingredients", response=list[ModelIngredientSchema])
def list_ingredients(_request):
    return Ingredient.objects.all()


@api.get("/recipe-ingredients", response=list[ModelRecipeIngredientSchema])
def list_recipe_ingredients(_request):
    return RecipeIngredient.objects.all()


@api.get("/all", response=list[RecipeSchema])
def recipe_data(_request):
    """
    Returns all recipes along with all the recipe ingredients that each contains.

    Because we join from RecipeIngredient, recipes without any recipe
    ingredients defined will not be returned.
    """
    # Iterate over data manually to prevent django from executing tons of subqueries
    all_data = RecipeIngredient.objects.select_related("recipe").order_by("recipe")
    recipes = []
    for _, group in groupby(all_data, key=lambda ri: ri.recipe.id):
        elements = list(group)
        recipes.append(RecipeSchema(recipe=elements[0].recipe, ingredients=elements))

    return recipes


urlpatterns = [
    path("recipes/", api.urls),
]
