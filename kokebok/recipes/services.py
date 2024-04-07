"""
This file contains business logic related to recipe creation, retrieval and/or updating
that is too complex to have in the api file directly.
"""

from django.forms import ValidationError
from ninja import File, UploadedFile
from recipes.embedding import embed_docs
from recipes.models import Recipe, RecipeEmbedding, RecipeIngredient
from recipes.api_schemas import FullRecipeCreationSchema, FullRecipeUpdateSchema
from django.db import transaction

HttpError = tuple[int, dict[str, str]]

def create_recipe(data: FullRecipeCreationSchema, hero_image: File[UploadedFile] | None):
    recipe_data = data.dict()
    ingredients = recipe_data.pop("ingredients")

    # Create model instances
    recipe = Recipe(**recipe_data, hero_image=hero_image)
    ris = [
        RecipeIngredient(recipe=recipe, **recipe_ingredient)
        for recipe_ingredient in ingredients
    ]

    # Perform a full clean of recipe and recipe ingredients before saving
    recipe.full_clean()
    for ri in ris:
        # Exclude recipe because it technically doesn't exist yet (before saving)
        ri.full_clean(exclude=["recipe"])

    # Create embeddings 
    raw_embeddings = embed_docs(
        recipe.title,
        recipe.preamble,
        recipe.instructions,
        recipe.rest_text,
    )
    embeddings = [
        RecipeEmbedding(
            recipe=recipe,
            embedding=raw_embed
        )
        for raw_embed in raw_embeddings
    ]

    # Save
    with transaction.atomic():
        recipe.save()
        for ri in ris:
            ri.save()
        for emb in embeddings:
            emb.save()

    return recipe


def update_recipe(recipe: Recipe, data: FullRecipeUpdateSchema, hero_image: File[UploadedFile] | None) -> Recipe | HttpError:
    """
    Returns the updated recipe and recipe ingredients

    Note the following logic for the ingredients (RecipeIngredient)
        * argument ingredients with ids are located and updated
        * argument ingredients without ids are created fresh and given ids
        * Existing recipe ingredients whose id are not included in the request data
            are deleted.
    """
    recipe_data = data.dict()
    recipe_ingredients = recipe_data.pop("ingredients")

    # Retrieve existing data
    existing_recipe_ingredients = RecipeIngredient.objects.filter(recipe_id=recipe.id)
    
    # If any text field has changed, recalculate the embeddings
    new_embeddings: list[RecipeEmbedding] = []
    if (
        recipe.title != recipe_data["title"] or 
        recipe.preamble != recipe_data["preamble"] or 
        recipe.instructions != recipe_data["instructions"] or 
        recipe.rest_text != recipe_data["rest_text"]
    ):
        raw_embeddings = embed_docs(
            recipe_data["title"],
            recipe_data["preamble"],
            recipe_data["instructions"],
            recipe_data["rest_text"],
        )
        new_embeddings = [
            RecipeEmbedding(
                recipe=recipe,
                embedding=raw_embed
            )
            for raw_embed in raw_embeddings
        ]

    # Perform updates
    # If this is slow, try deleting all ris and then creating all in the request instead
    try:
        with transaction.atomic(durable=True):
            for k, v in recipe_data.items():
                setattr(recipe, k, v)
            recipe.hero_image = hero_image
            recipe.save()

            # Delete ingredients missing from the request
            # Has to be performed before creation due to lazy django querying weirdness
            for ri in existing_recipe_ingredients:
                ri.delete()

            # Update or create ingredients included in the request
            for ri in recipe_ingredients:
                ri = RecipeIngredient(**ri, recipe_id=recipe.id)
                ri.full_clean()
                ri.save()

            if new_embeddings:
                RecipeEmbedding.objects.filter(recipe__id=recipe.id).delete()
                for emb in new_embeddings:
                    emb.save()

    except ValidationError as e:
        # TODO: change str(val) to something better
        return 403, {str(key): str(val) for key, val in e.error_dict.items()}
    
    recipe.refresh_from_db()

    return recipe