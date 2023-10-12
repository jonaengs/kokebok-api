import base64
from itertools import groupby

import ninja
from django.forms import ValidationError
from ninja import Field, ModelSchema, Router, Schema
from ninja.security import django_auth
from recipes.image_parsing import parse_img
from recipes.models import Ingredient, Recipe, RecipeIngredient
from recipes.scraping import scrape
from recipes.scraping.base import ScrapedRecipe

from kokebok import settings

router = Router(auth=ninja.constants.NOT_SET if settings.DEBUG else django_auth)


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


@router.get("recipes", response=list[ModelRecipeSchema])
def list_recipes(_request):
    return Recipe.objects.all()


@router.get("ingredients", response=list[ModelIngredientSchema])
def list_ingredients(_request):
    return Ingredient.objects.all()


@router.get("recipe-ingredients", response=list[ModelRecipeIngredientSchema])
def list_recipe_ingredients(_request):
    return RecipeIngredient.objects.all()


@router.get("all", response=list[RecipeSchema])
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


@router.get("scrape", response={200: ScrapedRecipe, 400: str})
def scrape_recipe(_request, url: str):
    existing = Recipe.objects.filter(origin_url=url).exists()
    if existing:
        return 403, "Recipe with given url already exists."

    recipe = scrape(url)
    try:
        recipe.clean()
    except ValidationError as e:
        return 403, {"message": e.message}

    return recipe


@router.get("vision", response={200: str, 404: str})
def test_vision(request):
    # TODO: Make POST, read image data from request
    if not settings.OCR_ENABLED:
        return 404, "OCR/Text-recognition service not enabled for this system"

    file = "img_w_text_6.jpg"
    with open(file, mode="rb") as f:
        data = f.read()

    b64_img = base64.b64encode(data)
    result = parse_img(b64_img)
    print(result)
    return result
