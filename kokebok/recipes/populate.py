from itertools import chain

from django.forms import model_to_dict
from recipes.models import Ingredient, Recipe, RecipeIngredient

_ingredients = [
    Ingredient(id=1001, name_no="fisk", name_de="fisch"),
    Ingredient(id=1002, name_en="water", name_de="wasser", is_ubiquitous=True),
    Ingredient(id=1003, name_no="salt", name_de="salz", is_ubiquitous=True),
    Ingredient(id=1004, name_no="gulrot", name_de="karotte"),
    Ingredient(id=1005, name_no="egg", name_de="ei"),
    Ingredient(id=1006, name_no="melk", name_de="milch"),
    Ingredient(id=1007, name_no="hvetemel"),
    Ingredient(id=1008, name_no="smør", name_de="butter"),
]

_recipes = [
    Recipe(
        id=1001,
        title="Fischsuppe",
        content="<h1>Die beste Fischsuppe der Welt!</h1>\n<p>\nSo schaffst du es: ...\n\n</p>",  # noqa
    ),
    Recipe(
        id=1002,
        title="Salzwasser",
        content="Geben Sie das Salz ins Wasser. Das ist alles. Du bist fertig!",  # noqa
    ),
    Recipe(
        id=1003,
        title="Pannekaker",
        content="Visp sammen egg, salt og melk. Tilsett mel og visp sammen til en klumpfri røre. La røra svelle ca 1/2 time. Rør den opp fra bunnen. Stek pannekaker. Server pannekaker med syltetøy eller sukker.",  # noqa
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
    # Pannekaker
    RecipeIngredient(
        name_in_recipe="egg",
        id=1007,
        recipe_id=1003,
        base_ingredient_id=1005,
        amount=2,
        unit="count",
    ),
    RecipeIngredient(
        name_in_recipe="salt",
        id=1008,
        recipe_id=1003,
        base_ingredient_id=1003,
        amount=1 / 4,
        unit="tsp",
    ),
    RecipeIngredient(
        name_in_recipe="melk",
        id=1009,
        recipe_id=1003,
        base_ingredient_id=1006,
        amount=6,
        unit="dl",
    ),
    RecipeIngredient(
        name_in_recipe="smør til steking",
        id=1010,
        recipe_id=1003,
        base_ingredient_id=1008,
        amount=0,
        unit="",
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
