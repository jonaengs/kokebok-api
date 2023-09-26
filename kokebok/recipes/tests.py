from django.forms import ValidationError
from django.test import TestCase
from recipes.models import Ingredient


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
