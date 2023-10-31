from itertools import groupby

import ninja
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.security import django_auth
from recipes.api_schemas import (
    FullRecipeCreationSchema,
    FullRecipeDetailSchema,
    FullRecipeListSchema,
    IngredientDetailSchema,
)
from recipes.image_parsing import parse_img
from recipes.models import Ingredient, Recipe, RecipeIngredient
from recipes.scraping import scrape
from recipes.scraping.base import ScrapedRecipe

from kokebok import settings

router = Router(
    auth=ninja.constants.NOT_SET if settings.DEBUG else django_auth, tags=["recipes"]
)


@router.post("recipes")
def recipe_add(request, recipe_schema: FullRecipeCreationSchema):
    recipe_data = recipe_schema.dict()
    ingredients = recipe_data.pop("ingredients")
    recipe = Recipe(**recipe_data)
    recipe.full_clean()

    ris = []
    for recipe_ingredient in ingredients:
        ri = RecipeIngredient(recipe=recipe, **recipe_ingredient.dict())
        ri.full_clean(exclude=["recipe"])  # Recipe doesn't exist yet
        ris.append(ri)

    recipe.save()
    for ri in ris:
        ri.save()

    return {"id": recipe.id}


@router.get("recipes", response=list[FullRecipeListSchema])
def recipe_list(_request):
    """
    Returns all recipes along with all the recipe ingredients that each contains.

    Because we join from RecipeIngredient, recipes without any recipe ingredients
    defined will not be returned. (Bug or feature? You decide!)
    """
    # Iterate over data manually to prevent django from executing tons of subqueries
    rec_ingrs = RecipeIngredient.objects.select_related("recipe").order_by("recipe")
    recipes = []
    for _, group in groupby(rec_ingrs, key=lambda ri: ri.recipe.id):
        elements = list(group)
        recipes.append(
            FullRecipeListSchema(**elements[0].recipe.__dict__, ingredients=elements)
        )

    return recipes


@router.get("recipes/{recipe_id}", response=FullRecipeDetailSchema)
def recipe_detail(request, recipe_id: int):
    qset = Recipe.objects.prefetch_related("recipe_ingredients")
    recipe = get_object_or_404(qset, id=recipe_id)
    return recipe


@router.get("ingredients", response=list[IngredientDetailSchema])
def ingredient_list(_request):
    return Ingredient.objects.all()


#
# Non-simple CRUD APIs below
#


@router.get("scrape", response={200: ScrapedRecipe, 400: str}, tags=["scrape"])
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


@router.post(
    "from_image", response={200: ScrapedRecipe, 400: str, 404: str}, tags=["scrape"]
)
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
