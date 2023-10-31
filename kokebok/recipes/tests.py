from django.forms import ValidationError
from django.test import RequestFactory, TestCase
from django.urls import reverse
from recipes.api import ingredient_list, recipe_detail, recipe_list
from recipes.models import Ingredient, Recipe


class IngredientTests(TestCase):
    def test_get_names(self):
        """
        Encodes current assumptions about ingredient names'
        order, number of, and value
        """
        egg = Ingredient(name_en="egg")
        egg_names = egg.get_names()
        self.assertEquals(egg_names, [None, "egg"] + [None] * 3)

        egg.name_no = "egg"
        egg_names = egg.get_names()
        self.assertEquals(egg_names, ["egg", "egg"] + [None] * 3)

    def test_ingredient_clean(self):
        # Ingredient must have at least one name
        with self.assertRaises(ValidationError):
            ingredient = Ingredient()
            ingredient.clean()

    def test_read_api_ok(self):
        Recipe.objects.create(title="t", id=123)
        views_and_args = [
            # Recipe
            (recipe_list, []),
            (recipe_detail, [123]),
            #
            (ingredient_list, []),
        ]
        request_factory = RequestFactory()
        for view, args in views_and_args:
            url = reverse("api-1.0.0:" + view.__name__, args=args)

            # Test without middleware using request factory
            request = request_factory.get(url)
            response = view(request, *args)
            # TODO: Test view return data

            # Test with middleware using TestClient
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_api_add_recipe_ok(self):
        # TODO: Try more complex cases
        url = reverse("api-1.0.0:" + "recipe_add")
        data = {"title": "test_title", "ingredients": []}
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
