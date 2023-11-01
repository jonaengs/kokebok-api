from collections import Counter
from itertools import groupby

import ninja
from django.db import transaction
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.security import django_auth
from recipes.api_schemas import (
    FullRecipeCreationSchema,
    FullRecipeDetailSchema,
    FullRecipeListSchema,
    FullRecipeUpdateSchema,
    IngredientCreationSchema,
    IngredientDetailSchema,
    IngredientUpdateSchema,
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
def recipe_add(request, full_recipe: FullRecipeCreationSchema):
    recipe_data = full_recipe.dict()
    ingredients = recipe_data.pop("ingredients")

    # Create model instances
    recipe = Recipe(**recipe_data)
    ris = [
        RecipeIngredient(recipe=recipe, **recipe_ingredient)
        for recipe_ingredient in ingredients
    ]

    # Perform a full clean of recipe and recipe ingredients before saving
    recipe.full_clean()
    for ri in ris:
        # Exclude recipe because it technically doesn't exist yet (before saving)
        ri.full_clean(exclude=["recipe"])

    # Save
    with transaction.atomic():
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
            FullRecipeListSchema(
                **elements[0].recipe.__dict__, recipe_ingredients=elements
            )
        )

    return recipes


@router.get("recipe/{recipe_id}", response=FullRecipeDetailSchema)
def recipe_detail(request, recipe_id: int):
    qset = Recipe.objects.prefetch_related("recipe_ingredients")
    recipe = get_object_or_404(qset, id=recipe_id)
    return recipe


@router.put("recipe/{recipe_id}", response={200: FullRecipeDetailSchema, 403: str})
def recipe_update(request, recipe_id: int, full_recipe: FullRecipeUpdateSchema):
    """
    Returns the update recipe and recipe ingredients

    Note the following logic for the ingredients (RecipeIngredient)
        * argument ingredients with ids are located and updated
        * argument ingredients without ids are created fresh and given ids
        * Existing recipe ingredients whose id are not included in the request data
            are deleted.
    """
    recipe_data = full_recipe.dict()
    ingredients = recipe_data.pop("ingredients")

    # Retrieve existing data
    recipe_qs = Recipe.objects.filter(id=recipe_id)
    recipe_ingredients = RecipeIngredient.objects.filter(recipe_id=recipe_id)

    # Validation
    recipe = get_object_or_404(recipe_qs, id=recipe_id)  # error if recipe id not found
    _id_counter = Counter(ri["id"] for ri in ingredients)
    if max(_id_counter.values()) > 1:
        return 403, "Duplicate ingredient id detected"

    # Perform updates
    # If this is slow, try deleting all ris and then creating all in the request instead
    with transaction.atomic():
        recipe_qs.update(**recipe_data)

        # Delete ingredients missing from the request
        # Has to be performed before creation due to lazy django querying weirdness
        sent_ri_ids = set(_id_counter.keys())
        missing_ris = recipe_ingredients.exclude(id__in=sent_ri_ids)
        for existing_ingredient in missing_ris:
            existing_ingredient.delete()

        # Update or create ingredients included in the request
        for ingredient in ingredients:
            if not ingredient.get("id") is None:
                ri = recipe_ingredients.filter(id=ingredient["id"])
                ri.update(**ingredient)
            else:
                RecipeIngredient.objects.create(**ingredient, recipe_id=recipe.id)

    recipe.refresh_from_db()
    return recipe


@router.delete("recipe/{recipe_id}", response=FullRecipeDetailSchema)
def recipe_delete(_request, recipe_id: int):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    # We rely on the delete=cascade setting deleting recipe ingredients here
    recipe.delete()
    recipe.id = recipe_id  # id is set to None on deletion
    return recipe


@router.get("ingredients", response=list[IngredientDetailSchema])
def ingredient_list(_request):
    return Ingredient.objects.all()


@router.post("ingredients", response=IngredientDetailSchema)
def ingredient_add(_request, ingredient: IngredientCreationSchema):
    ingredient = Ingredient.objects.create(**ingredient.dict())
    return ingredient


@router.put("ingredients/{ingredient_id}", response=IngredientDetailSchema)
def ingredient_update(
    _request, ingredient_id: int, ingredient_data: IngredientUpdateSchema
):
    ingredient_qs = Ingredient.objects.filter(id=ingredient_id)
    ingredient = get_object_or_404(ingredient_qs, id=ingredient_id)
    ingredient_qs.update(**ingredient_data.dict())
    ingredient.refresh_from_db()
    return ingredient


@router.delete("ingredients/{ingredient_id}", response=IngredientDetailSchema)
def ingredient_delete(_request, ingredient_id: int):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    ingredient.delete()
    ingredient.id = ingredient_id  # id is set to None on deletion
    return ingredient


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
