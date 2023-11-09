import base64
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q
from django.forms import ValidationError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from ninja.responses import NinjaJSONEncoder
from recipes.api import recipe_update
from recipes.api_schemas import (
    FullRecipeDetailSchema,
    FullRecipeListSchema,
    FullRecipeUpdateSchema,
    IngredientDetailSchema,
    RecipeIngredientUpdateSchema,
)
from recipes.models import Ingredient, Recipe, RecipeIngredient

from kokebok import settings


class RecipeTests(TestCase):
    # Use in-memory storage so test doesn't polute local file system
    # TODO: Should likely be applied to all tests. Maybe using a custom test runner
    # see
    # * https://docs.djangoproject.com/en/4.1/topics/testing/tools/#overriding-settings
    # * https://docs.djangoproject.com/en/4.2/topics/testing/advanced/
    # * https://stackoverflow.com/questions/7447134/how-do-you-set-debug-to-true-when-running-a-django-test
    # * https://stackoverflow.com/a/17066553
    @override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "staticfiles": settings.static_files_storage,
        }
    )
    def test_recipe_update_img_set_on_success(self):
        # tiny gif source: https://stackoverflow.com/a/15960901
        tiny_gif = "R0lGODlhAQABAAAAACH5BAEAAAAALAAAAAABAAEAAAIBAAA="  # base64
        rec = Recipe.objects.create(title="old title", id=111)

        # Assert that images don't currently exist
        with self.assertRaises((FileNotFoundError, ValueError)):
            rec.hero_image.open()
            rec.thumbnail.open()

        rec.hero_image = SimpleUploadedFile("t2.gif", base64.b64decode(tiny_gif))
        rec.save()

        self.assertTrue(rec.hero_image)
        self.assertTrue(rec.thumbnail)
        # Check that images do exist
        rec.hero_image.open()
        rec.thumbnail.open()

    @override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "staticfiles": settings.static_files_storage,
        }
    )
    def test_recipe_update_img_removal(self):
        # tiny gif source: https://stackoverflow.com/a/15960901
        tiny_gif = "R0lGODlhAQABAAAAACH5BAEAAAAALAAAAAABAAEAAAIBAAA="  # base64
        rec = Recipe.objects.create(
            title="old title",
            id=111,
            hero_image=SimpleUploadedFile("t.gif", base64.b64decode(tiny_gif)),
        )

        # Check that images do exist before update
        rec.hero_image.open()
        rec.thumbnail.open()

        rec.hero_image = None
        rec.save()

        # Make sure images set to None
        self.assertFalse(rec.hero_image)
        self.assertFalse(rec.thumbnail)

        with self.assertRaises((FileNotFoundError, ValueError)):
            rec.hero_image.open()
            rec.thumbnail.open()


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
            id=231, name_in_recipe="ri", recipe=rec, base_ingredient=ingr
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

        url = reverse("api-1.0.0:recipe_detail", args=[rec.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        returned_recipe = json.loads(response.content)
        _recipe_override = {
            "hero_image": "",  # fix blank imagefield being turned into None
            "thumbnail": "",  # ditto
            "recipe_ingredients": list(rec.recipe_ingredients.all()),
        }
        recipe_as_schema = FullRecipeDetailSchema(**rec.__dict__ | _recipe_override)
        # TODO: Figure out why ninja is being so difficult the images
        recipe_as_schema.hero_image = None
        recipe_as_schema.thumbnail = None
        expected_ingredient = self._as_api_response_data(recipe_as_schema)
        self.assertEqual(returned_recipe, expected_ingredient)

    def test_recipe_add(self):
        # Create base ingredient for RecipeIngredient to refer to
        Ingredient.objects.create(id=123, name_en="ingredient")

        url = reverse("api-1.0.0:recipe_add")
        recipe_data = {
            "title": "test_title",
            "ingredients": [{"name_in_recipe": "ingr", "base_ingredient_id": 123}],
        }
        form = {"hero_image": "", "full_recipe": json.dumps(recipe_data)}
        response = self.client.post(url, form)

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

        url = reverse("api-1.0.0:recipe_update", args=[rec.id])
        # Define data to PUT
        recipe_data = {
            "title": "new title",
            "ingredients": [
                {"id": 333, "name_in_recipe": "new name", "base_ingredient_id": 222},
                {"name_in_recipe": "add me", "base_ingredient_id": 222},
            ],
        }

        form = {"hero_image": "", "full_recipe": json.dumps(recipe_data)}
        response = self.client.post(url, data=form)
        self.assertEqual(response.status_code, 200, msg=response.content)

        # Check that Recipe and RecipeIngredients were updated as expected
        self.assertEqual(rec.title, "old title")
        self.assertEqual(ri_to_rename.name_in_recipe, "rename me")
        rec.refresh_from_db()
        ri_to_rename.refresh_from_db()
        self.assertEqual(rec.title, "new title")
        self.assertEqual(ri_to_rename.name_in_recipe, "new name")
        # Check that response data matches db data
        resp_data = json.loads(response.content)
        self.assertEqual(resp_data["title"], "new title")
        self.assertEqual(resp_data["ingredients"][0]["name_in_recipe"], "new name")

        # Check deletion and creation
        with self.assertRaises(RecipeIngredient.DoesNotExist):
            ri_to_delete.refresh_from_db()
        RecipeIngredient.objects.get(Q(recipe_id=rec.id) & Q(name_in_recipe="add me"))

        # Make sure we didn't create any objects
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(RecipeIngredient.objects.count(), 2)

    @override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "staticfiles": settings.static_files_storage,
        }
    )
    def test_recipe_update_no_img_replacement_on_err(self):
        tiny_gif = "R0lGODlhAQABAAAAACH5BAEAAAAALAAAAAABAAEAAAIBAAA="  # base64
        rec = Recipe.objects.create(
            title="old title",
            id=111,
            hero_image=SimpleUploadedFile("t_old.gif", base64.b64decode(tiny_gif)),
        )

        data = FullRecipeUpdateSchema(
            title="new title",
            ingredients=[
                RecipeIngredientUpdateSchema(
                    name_in_recipe="new name",
                    base_ingredient_id=0,  # err id
                )
            ],
        )
        hero_image = SimpleUploadedFile("t_new.gif", base64.b64decode(tiny_gif))

        url = reverse("api-1.0.0:recipe_update", args=[rec.id])
        req = RequestFactory().put(url)
        # Ensure on_commit callback is executed before continuing
        with self.captureOnCommitCallbacks(execute=True) as _:  # Don't need callbacks
            _ = recipe_update(req, rec.id, full_recipe=data, hero_image=hero_image)

        rec.refresh_from_db()
        self.assertEqual(rec.hero_image.name, "recipes/hero_images/t_old.gif")
        self.assertEqual(rec.thumbnail.name, "recipes/thumbnails/t_old.gif")
        # Make sure no errors are raised after refresh
        rec.hero_image.open()
        rec.thumbnail.open()

    @override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "staticfiles": settings.static_files_storage,
        }
    )
    def test_recipe_update_img_replaced_on_success(self):
        tiny_gif = "R0lGODlhAQABAAAAACH5BAEAAAAALAAAAAABAAEAAAIBAAA="  # base64
        rec = Recipe.objects.create(
            title="old title",
            id=111,
            hero_image=SimpleUploadedFile("t_old.gif", base64.b64decode(tiny_gif)),
        )
        ingr = Ingredient.objects.create(name_en="iii", id=222)

        data = FullRecipeUpdateSchema(
            title="new title",
            ingredients=[
                RecipeIngredientUpdateSchema(
                    name_in_recipe="new name",
                    base_ingredient_id=ingr.id,
                )
            ],
        )
        hero_image = SimpleUploadedFile("t_new.gif", base64.b64decode(tiny_gif))

        url = reverse("api-1.0.0:recipe_update", args=[rec.id])
        req = RequestFactory().put(url)
        # Ensure on_commit callback is executed before continuing
        with self.captureOnCommitCallbacks(execute=True) as _:
            _ = recipe_update(req, rec.id, full_recipe=data, hero_image=hero_image)

        with self.assertRaises(FileNotFoundError):
            rec.hero_image.open()
            rec.thumbnail.open()
        rec.refresh_from_db()
        self.assertEqual(rec.hero_image.name, "recipes/hero_images/t_new.gif")
        self.assertEqual(rec.thumbnail.name, "recipes/thumbnails/t_new.gif")
        # Make sure no errors are raised after refresh
        rec.hero_image.open()
        rec.thumbnail.open()

    def test_recipe_delete(self):
        # Setup test data
        rec = Recipe.objects.create(title="r", id=111)
        ingr = Ingredient.objects.create(name_en="iii", id=222)
        ri = RecipeIngredient.objects.create(
            id=333, name_in_recipe="ri", recipe=rec, base_ingredient=ingr
        )

        url = reverse("api-1.0.0:recipe_delete", args=[rec.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)

        # Assert deletion
        with self.assertRaises(Recipe.DoesNotExist):
            rec.refresh_from_db()
        with self.assertRaises(RecipeIngredient.DoesNotExist):
            ri.refresh_from_db()

        # Check response data (a little)
        self.assertEqual(json.loads(response.content)["id"], rec.id)

    def test_ingredient_add(self):
        data = {"name_no": "norsk test", "name_en": "english test"}
        url = reverse("api-1.0.0:ingredient_add")
        response = self.client.post(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 200, msg=response.content)

        ingredient_id = json.loads(response.content)["id"]
        self.assertTrue(Ingredient.objects.filter(id=ingredient_id).exists())
        self.assertEqual(Ingredient.objects.get(id=ingredient_id).name_no, "norsk test")
        self.assertEqual(Ingredient.objects.get(id=ingredient_id).name_it, None)

    def test_ingredient_update(self):
        # Update to change en name, remove no name and add de name
        # and set not ubiquitous (implicitly)
        ingr = Ingredient.objects.create(
            id=123, name_en="old name", name_no="deleteme", is_ubiquitous=True
        )
        data = {"name_en": "new name", "name_no": None, "name_de": "created name"}

        # Check operation ok
        url = reverse("api-1.0.0:ingredient_update", args=[ingr.id])
        response = self.client.put(url, data, content_type="application/json")
        self.assertEqual(response.status_code, 200, msg=response.content)

        # Check db data as expected
        ingr.refresh_from_db()
        self.assertEqual(ingr.name_en, "new name")
        self.assertIsNone(ingr.name_no)
        self.assertEqual(ingr.name_de, "created name")
        self.assertFalse(ingr.is_ubiquitous)

        # Check response data matches db data
        resp_data = json.loads(response.content)
        self.assertEqual(resp_data["name_en"], "new name")
        self.assertIsNone(resp_data["name_no"])
        self.assertEqual(resp_data["name_de"], "created name")
        self.assertFalse(resp_data["is_ubiquitous"])

    def test_ingredient_delete(self):
        ingr = Ingredient.objects.create(id=123, name_en="deleteme")
        url = reverse("api-1.0.0:ingredient_delete", args=[ingr.id])
        response = self.client.delete(url)

        # assert deletion
        with self.assertRaises(Ingredient.DoesNotExist):
            ingr.refresh_from_db()

        # check response contents
        ingredient_as_schema = IngredientDetailSchema.from_orm(ingr)
        expected_ingredient = self._as_api_response_data(ingredient_as_schema)
        self.assertEqual(json.loads(response.content), expected_ingredient)


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
