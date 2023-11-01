import json
import sys
from typing import TypedDict, get_args, get_type_hints

from django.core.exceptions import ImproperlyConfigured
from recipes.image_parsing.example_data import (
    example_input_pannekaker_med_fyll as example_recipe_text,
)
from recipes.image_parsing.example_data import (
    example_output_sardinomelett as example_chatgpt_output,
)
from recipes.image_parsing.text_parsing import text_to_recipe
from recipes.scraping import parse_ingredient_string
from recipes.scraping.base import ScrapedRecipe

from kokebok import settings

if settings.OCR_ENABLED:
    if settings.OCR_PROVIDER == "Google":
        from recipes.image_parsing.google_image_ocr import google_cloud_ocr as ocr
    else:
        raise ImproperlyConfigured("Selected OCR provider is not supported")


# TODO: Remove the alternative definition when we require Python >= 3.11
if sys.version_info >= (3, 11):
    from typing import NotRequired

    class GPTRecipe(TypedDict):
        title: NotRequired[str]
        preamble: NotRequired[str]
        content: NotRequired[str]
        yields: NotRequired[str | int | float]
        ingredients: dict[str, list[str]]
        instructions: list[str]

else:

    class RequiredKeys(TypedDict):
        ingredients: dict[str, list[str]]
        instructions: list[str]

    class GPTRecipe(RequiredKeys, total=False):
        title: str
        preamble: str
        content: str
        yields: str | int | float


MOCK_OCR = False
MOCK_GPT = False


def parse_img(img: bytes, gpt_hint: str = "", language: str = "") -> ScrapedRecipe:
    """
    Takes a base64-encoded image file and performs OCR on it before parsing the
    resulting text into a dictionary using ChatGPT. ChatGPT's structured output
    is then further transformed into the ScrapedRecipe format.
    """

    if not MOCK_OCR:
        img_text_content = ocr(
            img,
            {"language_hints": language} if language else {},
        )
        print(img_text_content)
    else:
        img_text_content = example_recipe_text

    if not MOCK_GPT:
        maybe_recipe_json = text_to_recipe(img_text_content, gpt_hint)
    else:
        maybe_recipe_json = example_chatgpt_output

    try:
        parsed_recipe: GPTRecipe = json.loads(maybe_recipe_json)
        # parsed_recipe = GPTRecipe(**parsed_response_dict)
    except Exception as e:
        print(e)
        raise ValueError("Error while converting ChatGPT output to json")

    formatted = _to_scraped_recipe(parsed_recipe)
    return formatted


def _to_scraped_recipe(parsed_recipe: GPTRecipe):
    def fill_with_defaults(d: dict, typd: type[TypedDict]) -> TypedDict:  # type: ignore[valid-type]  # noqa
        # Fills the dictionary's missing keys with default values
        def get_type(t: type) -> type:
            # return the first type in a Union or just T if T isn't a Union
            return t if not get_args(t) else get_args(t)[0]

        return {
            key: d.get(key) or get_type(t)()
            for key, t in get_type_hints(typd).items()
        }

    def join_instructions(instrs: list[str]) -> str:
        return "\n".join(f"{i}. " + instr for i, instr in enumerate(instrs, start=1))

    filled: GPTRecipe = fill_with_defaults(parsed_recipe, GPTRecipe)  # type: ignore[arg-type]  # noqa

    scraped_ingredients = {
        group_name: [
            parse_ingredient_string(ingredient, group_name)
            for ingredient in ingredients
        ]
        for group_name, ingredients in parsed_recipe["ingredients"].items()
    }
    instructions_str = join_instructions(filled["instructions"])

    overwrites = {
        "ingredients": scraped_ingredients,
        "content": instructions_str + "\n\n" + filled["content"],
    }
    as_scraped = ScrapedRecipe(**(filled | overwrites))
    return as_scraped
