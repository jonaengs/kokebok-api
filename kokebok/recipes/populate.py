from recipes.api_schemas import FullRecipeCreationSchema, RecipeIngredientCreationSchema
from recipes.services import create_recipe
from recipes.models import Ingredient, RecipeIngredient

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
    FullRecipeCreationSchema(
        title="Fischsuppe",
        instructions="<h1>Die beste Fischsuppe der Welt!</h1>\n<p>\nSo schaffst du es: ...\n\n</p>",  # noqa
        ingredients=[
            RecipeIngredientCreationSchema(
                base_ingredient_id=1001,
                name_in_recipe="Ein großer Fisch",
            ),
            RecipeIngredientCreationSchema(
                base_ingredient_id=1002,
                name_in_recipe="Wasser",
            ),
            RecipeIngredientCreationSchema(
                base_ingredient_id=1003,
                name_in_recipe="Eine Prise Salz",
            ),
            RecipeIngredientCreationSchema(
                base_ingredient_id=1004,
                name_in_recipe="Zwei in Scheiben geschnittene Karotten",
                is_optional=True,
            ),
        ]
    ),
    FullRecipeCreationSchema(
        title="Salzwasser",
        instructions="Geben Sie das Salz ins Wasser. Das ist alles. Du bist fertig!",  # noqa
        ingredients=[
            RecipeIngredientCreationSchema(
                base_ingredient_id=1002,
                name_in_recipe="Ein glas Wasser",
            ),
            RecipeIngredientCreationSchema(
                base_ingredient_id=1003,
                name_in_recipe="Ein Teelöffel Salz",
            ),
        ]
    ),
    FullRecipeCreationSchema(
        title="Pannekaker",
        instructions="Visp sammen egg, salt og melk. Tilsett mel og visp sammen til en klumpfri røre. La røra svelle ca 1/2 time. Rør den opp fra bunnen. Stek pannekaker. Server pannekaker med syltetøy eller sukker.",  # noqa
        ingredients=[
            RecipeIngredient(
                name_in_recipe="egg",
                base_ingredient_id=1005,
                base_amount=2,
                unit="count",
            ),
            RecipeIngredient(
                name_in_recipe="salt",
                base_ingredient_id=1003,
                base_amount=1 / 4,
                unit="tsp",
            ),
            RecipeIngredient(
                name_in_recipe="melk",
                base_ingredient_id=1006,
                base_amount=6,
                unit="dl",
            ),
            RecipeIngredient(
                name_in_recipe="smør til steking",
                base_ingredient_id=1008,
                base_amount=0,
                unit="",
            ),
        ]
    ),
]

def insert_dummy_data():
    for ingredient in _ingredients:
        ingredient.save()

    for recipe_data in _recipes:
        create_recipe(
            recipe_data,
            None
        )
        
