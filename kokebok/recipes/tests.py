import json

from django.db.models import Q
from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse
from ninja.responses import NinjaJSONEncoder
from recipes.api_schemas import (
    FullRecipeDetailSchema,
    FullRecipeListSchema,
    IngredientDetailSchema,
)
from recipes.models import Ingredient, Recipe, RecipeIngredient


class APITests(TestCase):
    def _as_api_response_data(self, schema):
        # Transforms the given ninja schema instance in the same
        # manner that ninja's api does by default
        return json.loads(json.dumps(schema, cls=NinjaJSONEncoder))

    def test_recipe_list(self):
        # Setup test data
        rec = Recipe.objects.create(title="r", id=123)
        ingr = Ingredient.objects.create(name_en="i", id=321)
        _ = RecipeIngredient.objects.create(
            id=231,
            name_in_recipe="ri",
            recipe=rec,
            base_ingredient=ingr,
        )

        # Check response ok
        url = reverse("api-1.0.0:recipe_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Check data as exected
        returned_data = json.loads(response.content)
        self.assertEqual(len(returned_data), 1)
        returned_recipe = returned_data[0]
        # Turning recipe into schema requires a little bit of work
        _recipe_override = {
            "hero_image": "",  # fix blank imagefield being turned into None
            "recipe_ingredients": list(rec.recipe_ingredients.all()),
        }
        recipe_as_schema = FullRecipeListSchema(**rec.__dict__ | _recipe_override)
        expected_recipe = self._as_api_response_data(recipe_as_schema)
        self.assertEqual(returned_recipe, expected_recipe)

    def test_ingredient_list(self):
        ingr = Ingredient.objects.create(name_en="ingr", id=321)

        # Test with middleware and everything
        url = reverse("api-1.0.0:ingredient_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        returned_data = json.loads(response.content)
        self.assertEqual(len(returned_data), 1)
        returned_ingredient = returned_data[0]
        ingredient_as_schema = IngredientDetailSchema.from_orm(ingr)
        expected_ingredient = self._as_api_response_data(ingredient_as_schema)
        self.assertEqual(returned_ingredient, expected_ingredient)

    def test_recipe_detail(self):
        rec = Recipe.objects.create(title="t", id=123)

        url = reverse("api-1.0.0:recipe_detail", args=[123])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        returned_recipe = json.loads(response.content)
        _recipe_override = {
            "hero_image": "",  # fix blank imagefield being turned into None
            "recipe_ingredients": list(rec.recipe_ingredients.all()),
        }
        recipe_as_schema = FullRecipeDetailSchema(**rec.__dict__ | _recipe_override)
        # TODO: Figure out why ninja is being so difficult about this
        recipe_as_schema.hero_image = None
        expected_ingredient = self._as_api_response_data(recipe_as_schema)
        self.assertEqual(returned_recipe, expected_ingredient)

    def test_recipe_add(self):
        # Create base ingredient for RecipeIngredient to refer to
        Ingredient.objects.create(id=123, name_en="ingredient")

        url = reverse("api-1.0.0:" + "recipe_add")
        data = {
            "title": "test_title",
            "ingredients": [{"name_in_recipe": "ingr", "base_ingredient_id": 123}],
        }
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 200, msg=response.content)

        recipe_id = json.loads(response.content)["id"]

        # Assert that recipe exists as claimed,
        # and that its title matches the given title
        self.assertTrue(Recipe.objects.filter(id=recipe_id).exists())
        self.assertEqual(Recipe.objects.get(id=recipe_id).title, "test_title")

        # Check that exactly one RecipeIngredient exists for the recipe
        # and that its name matches the name given in the request
        created_ri = RecipeIngredient.objects.get(recipe_id=recipe_id)
        self.assertEqual(created_ri.name_in_recipe, "ingr")

    def test_recipe_update(self):
        """
        Updating a recipe can involve both adding and removing existing recipe
        ingredients. This test tests both cases, with one ri being deleted
        and one added in the same update request.
        """

        # Setup test data
        rec = Recipe.objects.create(title="old title", id=111)
        ingr = Ingredient.objects.create(name_en="i", id=222)
        ri_to_rename = RecipeIngredient.objects.create(
            id=333,
            name_in_recipe="rename me",
            recipe=rec,
            base_ingredient=ingr,
        )
        ri_to_delete = RecipeIngredient.objects.create(
            id=444,
            name_in_recipe="delete me",
            recipe=rec,
            base_ingredient=ingr,
        )

        # Define data to PUT
        data = {
            "title": "new title",
            "hero_image": "",
            "ingredients": [
                {"id": 333, "name_in_recipe": "new name", "base_ingredient_id": 222},
                {"name_in_recipe": "add me", "base_ingredient_id": 222},
            ],
        }

        # Check response ok
        url = reverse("api-1.0.0:recipe_update", args=[111])
        response = self.client.put(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 200, msg=response.content)

        # Check that Recipe and RecipeIngredients were updated as expected
        self.assertEqual("old title", rec.title)
        self.assertEqual("rename me", ri_to_rename.name_in_recipe)
        rec.refresh_from_db()
        ri_to_rename.refresh_from_db()
        self.assertEqual("new title", rec.title)
        self.assertEqual("new name", ri_to_rename.name_in_recipe)

        # Check deletion and creation
        with self.assertRaises(RecipeIngredient.DoesNotExist):
            ri_to_delete.refresh_from_db()
        RecipeIngredient.objects.get(Q(recipe_id=rec.id) & Q(name_in_recipe="add me"))

        # Make sure we didn't create any objects
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(RecipeIngredient.objects.count(), 2)

    def test_ingredient_add(self):
        data = {"name_no": "norsk test", "name_en": "english test"}
        url = reverse("api-1.0.0:ingredient_add")
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 200, msg=response.content)

        ingredient_id = json.loads(response.content)["id"]
        self.assertTrue(Ingredient.objects.filter(id=ingredient_id).exists())
        self.assertEqual(Ingredient.objects.get(id=ingredient_id).name_no, "norsk test")
        self.assertEqual(Ingredient.objects.get(id=ingredient_id).name_it, None)


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
