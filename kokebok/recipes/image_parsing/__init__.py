import json
from collections import defaultdict

from recipes.image_parsing.openai_with_vision import image_to_json
from recipes.scraping.base import ScrapedRecipe, ScrapedRecipeIngredient

MOCK_OCR = False
MOCK_GPT = False


def parse_img(img: bytes, gpt_hint: str = "", language: str = "") -> ScrapedRecipe:
    """
    Takes a base64-encoded image file and performs OCR on it before parsing the
    resulting text into a dictionary using ChatGPT. ChatGPT's structured output
    is then further transformed into the ScrapedRecipe format.

    NEW: With the introduction of gpt-4-vision, we can now perform the entire process
    using only the OpenAI API.
    """

    recipe_json = image_to_json(img, gpt_hint)
    parsed_json = json.loads(recipe_json)

    # To make the parsed recipe into a ScrapedRecipe, the following steps are required:
    # 1. Group ingredients by the their group name
    parsed_json["ingredients"] = group_ingredients(parsed_json["ingredients"])

    recipe = ScrapedRecipe(**parsed_json)

    return recipe


def group_ingredients(ingredients: list[ScrapedRecipeIngredient]):
    groups = defaultdict(list)
    for ingr in ingredients:
        groups[ingr.get("group_name", "")].append(ingr)

    return groups
