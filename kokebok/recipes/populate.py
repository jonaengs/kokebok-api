from itertools import chain

from django.forms import model_to_dict
from recipes.models import Ingredient, Recipe, RecipeIngredient

_ingredients = [
    Ingredient(id=1001, name_no="fisk", name_de="fisch"),
    Ingredient(id=1002, name_en="water", name_de="wasser", is_ubiquitous=True),
    Ingredient(id=1003, name_no="salt", name_de="salz", is_ubiquitous=True),
    Ingredient(id=1004, name_no="gulrot", name_de="karotte"),
]

_recipes = [
    Recipe(
        id=1001,
        title="Fischsuppe",
        description="<h1>Die beste Fischsuppe der Welt!</h1>\n<p>\nSo schaffst du es: ...\n\n</p>",  # noqa
    ),
    Recipe(
        id=1002,
        title="Salzwasser",
        description="Geben Sie das Salz ins Wasser. Das ist alles. Du bist fertig!",  # noqa
    ),
]

_recipe_ingredients = [
    # Fiskesuppe
    RecipeIngredient(
        id=1001,
        recipe_id=1001,
        base_ingredient_id=1001,
        name_in_recipe="Ein großer Fisch",
    ),
    RecipeIngredient(
        id=1002,
        recipe_id=1001,
        base_ingredient_id=1002,
        name_in_recipe="Wasser",
    ),
    RecipeIngredient(
        id=1003,
        recipe_id=1001,
        base_ingredient_id=1003,
        name_in_recipe="Eine Prise Salz",
    ),
    RecipeIngredient(
        id=1004,
        recipe_id=1001,
        base_ingredient_id=1004,
        name_in_recipe="Zwei in Scheiben geschnittene Karotten",
        is_optional=True,
    ),
    # Saltvann
    RecipeIngredient(
        id=1005,
        recipe_id=1002,
        base_ingredient_id=1002,
        name_in_recipe="Ein glas Wasser",
    ),
    RecipeIngredient(
        id=1006,
        recipe_id=1002,
        base_ingredient_id=1003,
        name_in_recipe="Ein Teelöffel Salz",
    ),
]


def insert_dummy_data():
    for instance in chain(_ingredients, _recipes, _recipe_ingredients):
        instance.clean()

        # Update object if it exists, insert if it doesn't
        model = type(instance)
        if existing := model.objects.filter(pk=instance.id):
            existing.update(**model_to_dict(instance))
        else:
            instance.save()
