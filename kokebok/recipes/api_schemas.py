from ninja import Field, ModelSchema
from recipes.models import Ingredient, Recipe, RecipeIngredient

# Terminology:
# "Full recipe": Recipe + associated recipe ingredients
# "ingredients" (in the context of a "full recipe"): RecipeIngredient objects
# "Recipe", "Ingredient", "Recipe Ingredient": mirrors of the models

####################
# Ingredient schemas
####################


class IngredientDetailSchema(ModelSchema):
    # TODO: Remove names and resolver. They're mostly here as a PoC
    names: list[str | None]

    class Config:
        model = Ingredient
        model_fields = "__all__"

    @staticmethod
    def resolve_names(obj):
        return obj.get_names()


class IngredientCreationSchema(ModelSchema):
    class Config:
        model = Ingredient
        model_exclude = ["id"]


class IngredientUpdateSchema(ModelSchema):
    class Config:
        model = Ingredient
        model_exclude = ["id"]


##########################
# RecipeIngredient schemas
##########################


class RecipeIngredientListSchema(ModelSchema):
    base_ingredient_id: int = Field(alias="base_ingredient.id")

    class Config:
        model = RecipeIngredient
        model_fields = ["name_in_recipe", "is_optional"]


class RecipeIngredientDetailSchema(ModelSchema):
    base_ingredient_id: int = Field(alias="base_ingredient.id")

    class Config:
        model = RecipeIngredient
        model_exclude = ["base_ingredient"]


class RecipeIngredientCreationSchema(ModelSchema):
    base_ingredient_id: int

    class Config:
        model = RecipeIngredient
        model_exclude = ["id", "recipe", "base_ingredient"]


class RecipeIngredientUpdateSchema(ModelSchema):
    base_ingredient_id: int
    id: int | None = None  # Optional when used with RecipeUpdateSchema

    class Config:
        model = RecipeIngredient
        model_exclude = ["id", "recipe", "base_ingredient"]


################
# Recipe schemas
################


class FullRecipeListSchema(ModelSchema):
    """
    Recipes and their (recipe) ingredients, but without detailed information
    like recipe content and instructions and recipe ingredient unit
    """

    ingredients: list[RecipeIngredientListSchema] = Field(alias="recipe_ingredients")

    class Config:
        model = Recipe
        model_fields = [
            "id",
            "title",
            "preamble",
            "thumbnail",
            "created_at",
            "total_time",
        ]


class FullRecipeDetailSchema(ModelSchema):
    """All fields of a recipe and all fields of its recipe ingredients"""

    ingredients: list[RecipeIngredientDetailSchema] = Field(alias="recipe_ingredients")

    class Config:
        model = Recipe
        model_fields = "__all__"


class FullRecipeCreationSchema(ModelSchema):
    """Creation schema for recipe with its recipe ingredients"""

    ingredients: list[RecipeIngredientCreationSchema]

    class Config:
        model = Recipe
        model_exclude = ["id", "created_at", "hero_image", "thumbnail"]


class FullRecipeUpdateSchema(ModelSchema):
    ingredients: list[RecipeIngredientUpdateSchema]
    """Update schema for recipe and recipe ingredients"""

    class Config:
        model = Recipe
        model_exclude = ["id", "created_at", "hero_image", "thumbnail"]
