from django.db import models
from django.forms import ValidationError


class Recipe(models.Model):
    title = models.CharField(max_length=200, blank=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    origin_url = models.URLField(blank=True)


class Ingredient(models.Model):
    name_no = models.CharField(max_length=64, unique=True, null=True, blank=True)
    name_en = models.CharField(max_length=64, unique=True, null=True, blank=True)
    name_de = models.CharField(max_length=64, unique=True, null=True, blank=True)
    name_fr = models.CharField(max_length=64, unique=True, null=True, blank=True)
    name_it = models.CharField(max_length=64, unique=True, null=True, blank=True)
    is_ubiquitous = models.BooleanField(default=False)

    def get_names(self) -> list[str | None]:
        """
        Returns the names of the ingredient as a list
        """
        return [
            self.__getattribute__(field.name)
            for field in self._meta.fields
            if field.name.startswith("name_")
        ]

    def clean(self):
        if not any(self.get_names()):
            raise ValidationError("Ingredient must have at least one name!")
        return super().clean()


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        to=Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    base_ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.PROTECT,
        related_name="recipe_ingredients",
    )
    name_in_recipe = models.CharField(max_length=64)
    is_optional = models.BooleanField(default=False)
