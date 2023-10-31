from django.core.validators import MinValueValidator
from django.db import models
from django.dispatch import receiver
from django.forms import ValidationError


class Recipe(models.Model):
    class Languages(models.Choices):
        NORWEGIAN = "no"
        ENGLISH = "en"
        GERMAN = "de"
        FRENCH = "fr"
        ITALIAN = "it"

        @classmethod
        def codes(cls) -> list[str]:
            return [ch[0] for ch in cls.choices]

    title = models.CharField(max_length=200, blank=False)
    preamble = models.TextField(blank=True, default="")
    content = models.TextField(blank=True, default="")
    hero_image = models.ImageField(blank=True, upload_to="recipes/hero_images")
    created_at = models.DateTimeField(auto_now_add=True)
    original_author = models.CharField(max_length=128, blank=True, default="")
    language = models.CharField(
        max_length=8, choices=Languages.choices, blank=True, default=""
    )

    total_time = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    # Recipe yields consists of two parts:
    # the number of items/servings, and the name of the item.
    # Thus, we can support both "5 cookies" and "2 servings"
    yields_type = models.CharField(
        blank=True, max_length=32, default=""
    )  # blank => "serving"  # noqa
    yields_number = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )

    # For example, if the recipe has an accompanying youtube video
    video_url = models.URLField(blank=True, default="")
    # Source url if scraped or otherwise retrieved from a web page
    origin_url = models.URLField(blank=True, null=True, unique=True)
    # For specifying any other sources: books, people, ...
    other_source = models.CharField(max_length=256, blank=True, default="")

    def __repr__(self) -> str:
        return f"<Recipe: {self.title}>"

    def __str__(self) -> str:
        return self.title


@receiver(models.signals.post_delete, sender=Recipe)
def recipe_delete_handler(instance: Recipe, *args, **kwargs):
    """Deletes images associated with a recipe when a recipe is deleted"""
    if instance.hero_image:
        instance.hero_image.delete(save=False)


class Ingredient(models.Model):
    # unique=True means that indexes are created automatically for these fields
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

    def __repr__(self) -> str:
        return "|".join(name for name in self.get_names() if name)

    def __str__(self) -> str:
        return repr(self)


class RecipeIngredient(models.Model):
    class Units(models.Choices):
        # Weight
        GRAM = "g"
        KILOGRAM = "kg"
        OUNCE = "oz"
        POUND = "lb"
        # Volume
        LITER = "l"
        DECILITER = "dl"
        CENTILITER = "cl"
        MILLILITER = "ml"
        CUP = "cup"
        TABLESPOON = "tbsp"
        TEASPOON = "tsp"
        # Other
        COUNT = "count"
        SLICE = "slice"
        CENTIMETRE = "cm"
        INCH = "inch"
        BLANK = ""

    recipe = models.ForeignKey(
        to=Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    base_ingredient = models.ForeignKey(
        to=Ingredient,
        on_delete=models.PROTECT,
        related_name="recipe_ingredients",
        blank=True,  # In case the base ingredient hasn't been added yet
    )
    name_in_recipe = models.CharField(max_length=128)
    is_optional = models.BooleanField(default=False)

    # Name of the sub-recipe the ingredient is part of. Optional.
    group_name = models.CharField(max_length=128, blank=True)

    # The amount to use when making the base recipe
    base_amount = models.FloatField(
        blank=True, default=0, validators=[MinValueValidator(0.0)]
    )
    unit = models.CharField(
        max_length=16,
        blank=True,
        choices=Units.choices,
        default=Units.BLANK,
    )

    def clean(self):
        return super().clean()

    def __repr__(self) -> str:
        return f"<{self.recipe.title}: {self.name_in_recipe}>"

    def __str__(self) -> str:
        return f"{self.recipe.title}: {self.name_in_recipe}"
