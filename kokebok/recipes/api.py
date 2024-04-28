import io
from itertools import chain, groupby

import ninja
import requests
from django.conf import settings
from django.core.files.images import ImageFile
from django.db import transaction
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from ninja import File, Router
from ninja.files import UploadedFile
from ninja.security import django_auth
from pgvector.django import CosineDistance

from recipes.api_schemas import (
    FullRecipeCreationSchema,
    FullRecipeDetailSchema,
    FullRecipeListSchema,
    FullRecipeUpdateSchema,
    IngredientCreationSchema,
    IngredientDetailSchema,
    IngredientUpdateSchema,
)
from recipes.embedding import embed_query
from recipes.image_parsing import parse_img
from recipes.models import Ingredient, Recipe, RecipeEmbedding, RecipeIngredient
from recipes.scraping import scrape
from recipes.scraping.base import IngredientGroupDict, ScrapedRecipe
from recipes.services import create_recipe, get_recipe_embeddings, update_recipe

router = Router(
    auth=ninja.constants.NOT_SET if settings.DEBUG else django_auth, tags=["recipes"]
)


@router.post("recipes")
def recipe_add(
    request,
    full_recipe: FullRecipeCreationSchema,
    hero_image: UploadedFile | None = File(None),
):
    recipe = create_recipe(full_recipe, hero_image)

    return {"id": recipe.pk}


@router.get("recipes", response=list[FullRecipeListSchema])
def recipe_list(request):
    """
    Returns all recipes along with all the recipe ingredients that each contains.

    Because we join from RecipeIngredient, recipes without any recipe ingredients
    defined will not be returned. (Bug or feature? You decide!)
    """
    # Iterate over data manually to prevent django from executing tons of subqueries
    rec_ingrs = RecipeIngredient.objects.select_related("recipe").order_by("recipe")
    recipes = []
    for _, group in groupby(rec_ingrs, key=lambda ri: ri.recipe.pk):
        recipe_ingredients = list(group)
        recipe = recipe_ingredients[0].recipe
        recipes.append(
            recipe.__dict__
            | {
                "recipe_ingredients": recipe_ingredients,
                "thumbnail": recipe.thumbnail and recipe.thumbnail.url,
            }
        )

    return recipes


@router.get("recipe/{recipe_id}", response=FullRecipeDetailSchema)
def recipe_detail(request, recipe_id: int):
    qset = Recipe.objects.prefetch_related("recipe_ingredients")
    recipe = get_object_or_404(qset, id=recipe_id)
    return recipe


# POST because Django does not allow files in PUT requests (nor PATCH requests)
@router.post("recipe/{recipe_id}", response={200: FullRecipeDetailSchema, 403: dict})
def recipe_update(
    request,
    recipe_id: int,
    full_recipe: FullRecipeUpdateSchema,
    hero_image: UploadedFile | None = File(None),
):
    recipe_qs = Recipe.objects.filter(id=recipe_id)
    original_recipe = get_object_or_404(
        recipe_qs, id=recipe_id
    )  # error if recipe id not found

    updated_recipe = update_recipe(original_recipe, full_recipe, hero_image)

    return updated_recipe


@router.delete("recipe/{recipe_id}", response=FullRecipeDetailSchema)
def recipe_delete(request, recipe_id: int):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    # We rely on the delete=cascade setting deleting recipe ingredients here
    recipe.delete()
    recipe.id = recipe_id  # id is set to None on deletion
    return recipe


@router.get("ingredients", response=list[IngredientDetailSchema])
def ingredient_list(request):
    return Ingredient.objects.all()


@router.post("ingredients", response=IngredientDetailSchema)
def ingredient_add(request, ingredient: IngredientCreationSchema):
    ingredient = Ingredient.objects.create(**ingredient.dict())
    return ingredient


@router.put("ingredients/{ingredient_id}", response=IngredientDetailSchema)
def ingredient_update(
    request, ingredient_id: int, ingredient_data: IngredientUpdateSchema
):
    ingredient_qs = Ingredient.objects.filter(id=ingredient_id)
    ingredient = get_object_or_404(ingredient_qs, id=ingredient_id)
    ingredient_qs.update(**ingredient_data.dict())
    ingredient.refresh_from_db()
    return ingredient


@router.delete("ingredients/{ingredient_id}", response=IngredientDetailSchema)
def ingredient_delete(request, ingredient_id: int):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    ingredient.delete()
    ingredient.id = ingredient_id  # id is set to None on deletion
    return ingredient


#
# Non-simple CRUD APIs below
#


@router.get("search", tags=["search"])
def search(request, query: str):
    query_embedding = embed_query(query)

    # Sanity checking
    simlarities = (
        RecipeEmbedding.objects.annotate(
            distance=CosineDistance("embedding", query_embedding)
        )
        .prefetch_related("recipe")
        .order_by("distance")
        .values_list("recipe__title", "distance")
        .all()
    )
    print(*[tuple(s) for s in simlarities], sep="\n")

    # TODO: Get distinct recipe_id working with distance ordering
    embeds = (
        RecipeEmbedding.objects.order_by(CosineDistance("embedding", query_embedding))
        .prefetch_related("recipe")
        .values_list("recipe__title", flat=True)
        .all()
    )

    recipe_ids = list({rid: 0 for rid in embeds}.keys())[:10]

    return recipe_ids


@router.get(
    "scrape", response={200: ScrapedRecipe, 400: str, 403: str}, tags=["scrape"]
)
def scrape_recipe(request, url: str):
    existing = Recipe.objects.filter(origin_url=url).exists()
    if existing:
        return 403, "Recipe with given url already exists."

    scraped_data: ScrapedRecipe = scrape(url)
    try:
        scraped_data.clean()
    except ValidationError as e:
        return 403, {"message": e.message}

    return scraped_data


@router.get("scrape_bad", response={200: str, 403: str}, tags=["scrape"])
def scrape_recipe_bad(request, url: str):
    """
    Creates a recipe and ingredients with norwegian names from the given url.
    Only to be used for quick prototyping/testing purposes.!

    TODO: Remove this. It's just for quickly getting some data going
    """
    existing = Recipe.objects.filter(origin_url=url).exists()
    if existing:
        return 403, "Recipe with given url already exists."

    scraped_recipe = scrape(url)
    scraped_dict = scraped_recipe.dict()
    ingredients: IngredientGroupDict = scraped_dict.pop("ingredients")

    hero_image_link = scraped_dict.pop("hero_image_link")
    if hero_image_link:
        image_data = requests.get(hero_image_link).content
        image_name = hero_image_link.split("/")[-1]  # hacky but it works for now
        hero_image = ImageFile(io.BytesIO(image_data), name=image_name)
        scraped_dict["hero_image"] = hero_image

    with transaction.atomic():
        recipe = Recipe.objects.create(**scraped_dict)

        ingredients_list = chain(*ingredients.values())
        for ingredient in ingredients_list:
            ingredient_dict = ingredient.dict()
            ingredient_name_no = ingredient_dict.pop("base_ingredient_str")
            try:
                base_ingredient = Ingredient.objects.get(name_no=ingredient_name_no)
            except Ingredient.DoesNotExist:
                base_ingredient = Ingredient.objects.create(name_no=ingredient_name_no)
            RecipeIngredient.objects.create(
                recipe=recipe, **ingredient_dict, base_ingredient=base_ingredient
            )

        embeddings = get_recipe_embeddings(recipe)
        for emb in embeddings:
            emb.save()

    return "ok"


@router.post(
    "from_image", response={200: ScrapedRecipe, 400: str, 404: str}, tags=["scrape"]
)
def recipe_from_image(request, img: UploadedFile):
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
