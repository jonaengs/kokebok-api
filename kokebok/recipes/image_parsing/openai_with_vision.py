import base64
import math
from typing import Any

import openai

SYSTEM_PROMPT = """
Your task is to extract text from an image and turn it into structured data.
Specifically, you will receive an image of a cooking recipe whose text content
you will turn into a JSON object with a set structure.

The JSON structure can be described by the following TypeScript definition:
```
type Recipe = {
    // the recipe title
    title: string;
    // A short introductory text following the title
    preamble?: string;
    // The cooking instructions. Takes the form of a numbered markdown list
    instructions: string;
    // Any remaining text content in the recipe that does not fit in the above fields
    rest_text: string;

    // the time estimate for making the recipe
    total_time?: number;

    // The author of the recipe
    original_author?: string;
    // ISO 639-1 code identifying the language of the recipe
    language?: string;

    // What is yielded by the recipe: muffins, servings, cookies, ...
    yields_type?: string;
    // The number of <yields_type> which the recipe yields. Must be an integer.
    yields_number?: number;

    // The ingredients used in the recipe. Note that this is an array of objects.
    // also note that the same ingredient may appear multiple times, for example if used in multiple sub-recipes
    ingredients: {
        // The name of just the ingredient with any fluff removed. E.g., "2 unripe bananas, peeled" becomes "banana"
        base_ingredient_name: string;
        // The name/description of the ingredient as it appears in the recipe
        name_in_recipe: string;
        // If the ingredient is part of a "sub-recipe grouped together with other ingredients under some header, then the group name is that header string
        group_name?: string;
        // The amount of the ingredient which should be used
        base_amount?: number;
        // The unit in which the ingredient is measured: grams, ounces, etc.
        // Should always use the shortened string version of the unit. "g" instead of "grams", "oz" instead of "ounces" and so on
        unit?: string;
        // Whether the ingredient may be omitted from the recipe or not. Defaults to false.
        is_optional: boolean;
    }[]
}
```

The user input will be the image of the recipe. You will reply with ONLY the JSON
describing the recipe. You will NOT output anything other than the JSON structure.

Your job is to recreate the recipe text exactly. Do not add to, embelish or change
any of the recipe contents. Keep the original language intact and do not translate anything.


Here is an example recipe JSON object:
{
    "title": "Pancakes with homemade blueberry jam",
    "preamble": "The world's most delicious pancakes with the world's best jam. Don't miss it!"
    "instructions": "1. Create the pancake batter as instructed on the packet\n\n2. Leave the batter to swell\n\n3. Mix the blueberries and sugar, before crushing them with a fork\n\n4. Fry the pancakes\n\n5. Serve the fresh pancakes with your delicious homemade blueberry jam",
    "yields_type": "serving"
    "yields_number": 2,
    "rest_text": "This is an old family recipe passed down for generations. I still remember the smell in the kitchen when my grandpa cooked it for our family when we visisted him on vacation when I was little..."
    "ingredients": [
        {
            "name_in_recipe": "pancake mix",
            "base_ingredient_name": "pancake mix",
            "group_name": "The Pancakes",
            "base_amount": 1,
        },
        {
            "name_in_recipe": "unsalted butter for frying",
            "base_ingredient_name": "unsalted butter",
            "group_name": "The Pancakes",
        },
        {
            "name_in_recipe": "unsalted butter for frying",
            "base_ingredient_name": "unsalted butter",
            "group_name": "The Pancakes",
        },
        {
            "name_in_recipe": "fresh blueberries",
            "base_ingredient_name": "blueberry",
            "group_name": "Blueberry Jam",
            "base_amount": 300,
            "unit": "g"
        },
        {
            "name_in_recipe": "granluated sugar",
            "base_ingredient_name": "sugar",
            "group_name": "Blueberry Jam",
            "base_amount": 100,
            "unit": "g"
        },
    ],
}

""".strip()


USER_HINT_PREAMBLE = """
You have been provided with the following hint to help you parse the image correctly:
{HINT}
""".strip()


model = "gpt-4-turbo"
price_1k_tokens = 0.01  # in dollars



def image_to_json(img_data: bytes, user_hint: str = "") -> str:
    full_user_text = USER_HINT_PREAMBLE.format(HINT=user_hint) if user_hint else ""

    # Pricing calculations
    estimate_system_prompt_tokens = len(SYSTEM_PROMPT) / 3.5
    estimate_user_text_tokens = len(full_user_text) / 2.5
    estimate_image_tiles = len(img_data) / (512 * 512)
    estimate_user_image_tokens = 85 + 170 * estimate_image_tiles
    estimate_total_input_tokens = math.ceil(
        estimate_system_prompt_tokens
        + estimate_user_text_tokens
        + estimate_user_image_tokens
    )
    print(f"{estimate_total_input_tokens=}")
    estimate_input_cost = (estimate_total_input_tokens / 1000) * price_1k_tokens
    print(f"{estimate_input_cost=}")

    # Construct the chat messages
    chat_messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if user_hint:
        chat_messages.append({"role": "system", "content": full_user_text})

    img_b64 = base64.b64encode(img_data).decode("utf-8")
    chat_messages.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "please convert this image to JSON."},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{img_b64}"},
            ],
        }
    )

    # chat API docs: https://platform.openai.com/docs/api-reference/chat/create
    response = openai.ChatCompletion.create(
        presence_penalty=-1,  # Discourage new topics
        temperature=0.2,  # Make model more predictable
        model=model,
        messages=chat_messages,
        response_format={"type": "json_object"},  # Make sure output is JSON
        stream=False,
        max_tokens=4096,
    )
    print(response)

    if response["choices"][0]["finish_reason"] == "content_filter":
        raise ValueError("ChatGPT stopped due to content filter.")

    # More costs reporting
    input_cost = response["usage"]["prompt_tokens"] * price_1k_tokens / 1000
    output_cost = response["usage"]["completion_tokens"] * price_1k_tokens / 1000
    total_cost = input_cost + output_cost
    print("COSTS:")
    print(f"{input_cost=} ({estimate_input_cost=})")
    print(f"{output_cost=}")
    print(f"Total cost: ${total_cost} (~ equal to NOK {10*total_cost})")

    response_text: str = response["choices"][0]["message"]["content"]

    response_text = response_text.lstrip("```json")
    response_text = response_text.rstrip("```")

    print(response_text)
    return response_text
