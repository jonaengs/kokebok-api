from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from recipes.models import Ingredient, Recipe


class IngredientTests(TestCase):
    def test_get_names(self):
        """
        Encodes current assumptions about ingredient names'
        order, number of, and value
        """
        egg = Ingredient.objects.create(name_en="egg")
        egg_names = egg.get_names()
        self.assertEquals(egg_names, [None, "egg"] + [None] * 3)

        egg.name_no = "egg"
        egg_names = egg.get_names()
        self.assertEquals(egg_names, ["egg", "egg"] + [None] * 3)

    def test_ingredient_clean(self):
        # Ingredient must have at least one name
        make_f = lambda: Ingredient.objects.create().clean()  # noqa
        self.assertRaises(ValidationError, make_f)

    def test_read_api_ok(self):
        Recipe.objects.create(title="t", id=123)
        func_names = [
            # Recipe
            ("recipe_list", []),
            ("recipe_detail", [123]),
            ("recipe_overview", []),
            #
            ("ingredient_list", []),
            ("recipe_ingredient_list", []),
        ]
        url_names = [("api-1.0.0:" + s, args) for s, args in func_names]
        for url_name, args in url_names:
            url = reverse(url_name, args=args)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_api_add_recipe_ok(self):
        url = reverse("api-1.0.0:" + "recipe_add")
        data = {"recipe": {"title": "test_title"}, "ingredients": []}
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
