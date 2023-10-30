from itertools import groupby

import ninja
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
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


class BaseRecipeCreationSchema(ModelSchema):
    class Config:
        model = Recipe
        model_exclude = ["id", "created_at"]


class BaseRecipeIngredientCreationSchema(ModelSchema):
    base_ingredient_id: int

    class Config:
        model = RecipeIngredient
        model_exclude = ["id", "recipe", "base_ingredient"]


class RecipeCreationSchema(Schema):
    recipe: BaseRecipeCreationSchema
    ingredients: list[BaseRecipeIngredientCreationSchema]


@router.post("recipes")
def recipe_add(request, recipe_data: RecipeCreationSchema):
    recipe = Recipe(**recipe_data.recipe.dict())
    recipe.full_clean()

    ris = []
    for recipe_ingredient in recipe_data.ingredients:
        ri = RecipeIngredient(recipe=recipe, **recipe_ingredient.dict())
        ri.full_clean(exclude=["recipe"])  # Recipe doesn't exist yet
        ris.append(ri)

    recipe.save()
    for ri in ris:
        ri.save()

    return {"id": recipe.id}


@router.get("recipes", response=list[ModelRecipeSchema])
def recipe_list(_request):
    return Recipe.objects.all()


@router.get("recipes/{recipe_id}", response=ModelRecipeSchema)
def recipe_detail(request, recipe_id: int):
    return get_object_or_404(Recipe, id=recipe_id)


@router.get("ingredients", response=list[ModelIngredientSchema])
def ingredient_list(_request):
    return Ingredient.objects.all()


@router.get("recipe-ingredients", response=list[ModelRecipeIngredientSchema])
def recipe_ingredient_list(_request):
    return RecipeIngredient.objects.all()


@router.get("all", response=list[RecipeSchema])
def recipe_overview(_request):
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


@router.post("from_image", response={200: ScrapedRecipe, 400: str, 404: str})
def img_upload(request, img: ninja.files.UploadedFile):
    if not settings.OCR_ENABLED:
        return 404, "OCR/Text-recognition service not enabled for this system"

    img_data = img.read()

    try:
        recipe_data = parse_img(img_data)
        recipe_data.clean()
    except ValueError as e:
        return 400, str(e)
    except ValidationError as e:
        return 400, str(e)
    except Exception as e:
        raise e
        print(e)
        return 400, "An error occured."

    return recipe_data
