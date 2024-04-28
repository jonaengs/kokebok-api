from typing import Any

from django.test import TestCase

from recipes.scraping.scrapers.thewoksoflife import TheWoksOfLifeScraper
from recipes.scraping.tests._base_scraper_test import BaseScraperTest
from recipes.scraping.tests._utils import inject_base_tests, with_params

parameters: dict[str, dict[str, Any]] = {
    "thewoksoflife.red_curry_chicken.html": {
        "_url": "https://thewoksoflife.com/red-curry-chicken/",
        "title": "Thai Red Curry Chicken",
        "group_names": ["For the chicken:", "For the rest of the dish:"],
        "preamble": "This Thai red curry chicken recipe is a restaurant-quality dish with a great variety of flavors and textures. Serve with steamed rice, and dinner is set.",
        # Ingredient parsing tests:
        "_ingredient_paths": [
            ("For the chicken:", 0),  # chicken
            ("For the rest of the dish:", 6),  # red bell pepper
            ("For the rest of the dish:", 10),  # coconut milk
        ],
        "ingredient_amounts": [1, 1 / 2, 13.5],
        "ingredient_units": ["lb", "count", "oz"],
        "base_ingredient_names": [
            "boneless skinless chicken breast or thighs",
            "red bell pepper",
            "coconut milk",
        ],
        "full_ingredient_names": [
            "boneless skinless chicken breast or thighs (thinly sliced)",
            "red bell pepper",
            "coconut milk (13.5 ounces/400ml = 1 can)",
        ],
        "ingredient_is_optional": [False, False, False],
    },
    "thewoksoflife.pork_mustard_greens.html": {
        "_url": "https://thewoksoflife.com/pork-belly-pickled-mustard-greens-chinese/#recipe",
        "title": "Braised Pork Belly with Pickled Mustard Greens (酸菜卤肉饭)",
        "group_names": [""],
        "preamble": "This Braised Pork Belly with Pickled Mustard Greens (酸菜卤肉饭) is savory, tangy, and perfect over rice. The tang of the pickled vegetables wakes up your taste buds and cuts through the heaviness of the meat, making for a balanced, satisfying dish.",
        # Ingredient parsing tests:
        "_ingredient_paths": [
            ("", 1),  # pork belly
            ("", 11),  # water
        ],
        "ingredient_amounts": [1.5, 0],
        "ingredient_units": ["lb", ""],
        "base_ingredient_names": [
            "boneless skin-on pork belly",
            "water",
        ],
        "full_ingredient_names": [
            "boneless skin-on pork belly (can also use skinless pork belly)",
            "2-3 cups water",
        ],
        "ingredient_is_optional": [
            False,
            False,
        ],
    },
    "thewoksoflife.chicken_katsu.html": {
        "_url": "https://thewoksoflife.com/chicken-katsu-curry-rice/",
        "title": "Chicken Katsu Curry Rice",
        "group_names": [
            "For the curry sauce:",
            "For the chicken katsu:",
            "For serving:",
        ],
        "preamble": "This dish is a symphony of textures—crispy panko-breaded chicken cutlet, creamy curry sauce, and slightly sticky, beautifully translucent Japanese rice.",
        # Ingredient parsing tests:
        "_ingredient_paths": [
            ("For the curry sauce:", 4),  # Worcestershire sauce
            ("For serving:", 0),  # rice
        ],
        "ingredient_amounts": [1, 6],
        "ingredient_units": ["tsp", "cup"],
        "base_ingredient_names": [
            "Worcestershire sauce",
            "steamed short grain Japanese rice",
        ],
        "full_ingredient_names": [
            "Worcestershire sauce (optional)",
            "steamed short grain Japanese rice (such as koshihikari)",
        ],
        "ingredient_is_optional": [
            True,
            False,
        ],
    },
}


@with_params(parameters)
@inject_base_tests(
    exclude=[
        BaseScraperTest.test_content_text,
    ]
)
class TheWoksOfLifeTest(TestCase):
    scraper_cls = TheWoksOfLifeScraper
    # scraper: TheWoksOfLifeScraper = None  # Only here to help autocomplete

    def _check_ingredient_expected(self, expected: list[Any], field: str):
        my_ingredient_groups = self.scraper.my_ingredient_groups()
        for path, expected in zip(self._ingredient_paths, expected):
            group, idx = path
            ingredient = my_ingredient_groups[group][idx]
            actual = dict(ingredient)[field]
            self.assertEqual(actual, expected, f"[{field}] {ingredient}")

    def test_ingredient_amount(self):
        self._check_ingredient_expected(
            self.expected_ingredient_amounts,
            "base_amount",
        )

    def test_ingredient_unit(self):
        self._check_ingredient_expected(
            self.expected_ingredient_units,
            "unit",
        )

    def test_ingredient_base_name(self):
        self._check_ingredient_expected(
            self.expected_base_ingredient_names,
            "base_ingredient_str",
        )

    def test_ingredient_full_name(self):
        self._check_ingredient_expected(
            self.expected_full_ingredient_names,
            "name_in_recipe",
        )

    def test_ingredient_is_optional(self):
        self._check_ingredient_expected(
            self.expected_ingredient_is_optional,
            "is_optional",
        )
