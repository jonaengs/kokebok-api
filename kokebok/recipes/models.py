import io
import sys

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Q
from django.dispatch import receiver
from django.forms import ValidationError
from pgvector.django import IvfflatIndex, VectorField
from PIL import Image


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
    preamble = models.TextField(blank=True, null=True, default=None)
    instructions = models.TextField(blank=True, null=True, default=None)
    rest_text = models.TextField(blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(
        max_length=8, choices=Languages.choices, blank=True, default=None, null=True
    )
    total_time = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        default=None,
    )

    # Image fields.
    hero_image = models.ImageField(blank=True, upload_to="recipes/hero_images")
    thumbnail = models.ImageField(blank=True, upload_to="recipes/thumbnails")
    _replaced_image_fields: list[models.ImageField] = []  # Used for deleting old imgs

    # Recipe yields consists of two parts:
    # the number of items/servings, and the name of the item.
    # Thus, we can support both "5 cookies" and "2 servings"
    yields_type = models.CharField(
        null=True, blank=True, max_length=32, default=None
    )  # blank => "serving"  # noqa
    yields_number = models.IntegerField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )

    original_author = models.CharField(
        max_length=128, blank=True, null=True, default=None
    )
    # For example, if the recipe has an accompanying youtube video
    video_url = models.URLField(blank=True, null=True, default=None)
    # Source url if scraped or otherwise retrieved from a web page
    origin_url = models.URLField(blank=True, null=True, unique=True, default=None)
    # For specifying any other sources: books, people, ...
    other_source = models.CharField(max_length=256, blank=True, null=True, default=None)

    class Meta:
        constraints = [
            models.CheckConstraint(check=~Q(title__exact=""), name="title not empty"),
            models.CheckConstraint(
                check=~Q(preamble__exact=""), name="preamble not empty"
            ),
            models.CheckConstraint(
                check=~Q(instructions__exact=""), name="instructions not empty"
            ),
            models.CheckConstraint(
                check=~Q(rest_text__exact=""), name="rest_text not empty"
            ),
            models.CheckConstraint(
                check=~Q(original_author__exact=""), name="original_author not empty"
            ),
            models.CheckConstraint(
                check=~Q(other_source__exact=""), name="other_source not empty"
            ),
        ]

    def __repr__(self) -> str:
        return f"<Recipe: {self.title}>"

    def __str__(self) -> str:
        return self.title


@receiver(models.signals.post_delete, sender=Recipe)
def recipe_delete_handler(instance: Recipe, *args, **kwargs):
    """Deletes images associated with a recipe when a recipe is deleted"""
    if instance.hero_image:
        instance.hero_image.delete(save=False)
    if instance.thumbnail:
        instance.thumbnail.delete(save=False)


@receiver(models.signals.pre_save, sender=Recipe)
def recipe_thumbnail_updater(sender: type[Recipe], instance: Recipe, **kwargs):
    """Generates the thumbnail of recipe hero image on hero image addition/change"""
    # Thanks to https://stackoverflow.com/a/7934958 for idea of using pre_save signal

    def make_thumbnail(image_field: models.ImageField):
        # Thanks to https://stackoverflow.com/a/12309950 for implementation
        thumb_img = Image.open(image_field)
        thumb_img.thumbnail((512, 512))  # TODO: Figure out good thumbnail size
        thumb_data = io.BytesIO()
        # Use same format for thumbnail as for image
        thumb_img.save(thumb_data, thumb_img.format)
        thumb_file = InMemoryUploadedFile(
            file=thumb_data,
            field_name=None,
            name=image_field.name.split("/")[-1],
            content_type=Image.MIME[thumb_img.format],
            size=sys.getsizeof(thumb_data),
            charset=None,
        )
        return thumb_file

    try:
        existing = sender.objects.get(id=instance.id)
    except sender.DoesNotExist:
        # Instance is being created, so generate thumbnail
        if instance.hero_image:
            instance.thumbnail = make_thumbnail(instance.hero_image)
    else:
        # Instance hero image has changed
        if not existing.hero_image == instance.hero_image:
            if not instance.hero_image:  # hero image is being removed
                instance.thumbnail = instance.hero_image  # set blank
            else:
                instance.thumbnail = make_thumbnail(instance.hero_image)
            instance._replaced_image_fields = [existing.hero_image, existing.thumbnail]


# TODO: see if this can be done in the delete method using transaction.on_commit
# see: https://forum.djangoproject.com/t/pointers-and-tips-for-testing-imagefield-and-filefield-incl-deletion/11949/4
@receiver(models.signals.post_save, sender=Recipe)
def delete_replaced_images(sender: type[Recipe], instance: Recipe, **kwargs):
    """Deletes the recipe images recorded as having been replaced"""

    def do_delete():
        for img_field in instance._replaced_image_fields:
            img_field.delete(save=False)
        instance._replaced_image_fields = []  # just to be safe

    # Only perform the delete after the current transaction has committed (https://stackoverflow.com/a/52703242)
    transaction.on_commit(do_delete)


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
    class Units(models.TextChoices):
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
    name_in_recipe = models.CharField(max_length=128, blank=False)
    is_optional = models.BooleanField(default=False)

    # Name of the sub-recipe the ingredient is part of
    group_name = models.CharField(max_length=128, blank=True, null=True, default=None)

    # The amount to use when making the base recipe
    base_amount = models.FloatField(
        blank=True,
        validators=[MinValueValidator(0.0)],
        null=True,
        default=None,
    )
    unit = models.CharField(
        max_length=16,
        blank=True,
        choices=Units.choices,
        default=Units.BLANK,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(group_name__exact=""), name="group_name not empty"
            )
        ]

    def __repr__(self) -> str:
        return f"<{self.recipe.title}: {self.name_in_recipe}>"

    def __str__(self) -> str:
        return f"{self.recipe.title}: {self.name_in_recipe}"


class RecipeEmbedding(models.Model):
    recipe = models.ForeignKey(
        to=Recipe, on_delete=models.CASCADE, related_name="embeddings"
    )
    origin_field = "rest_text"
    # Embeddings are generated using Cohere's 'embed-multilingual-v3.0' model
    embedding = VectorField(dimensions=1024)

    class Meta:
        indexes = [
            IvfflatIndex(
                name="recipe_embeddings_ivf",
                fields=["embedding"],
                # TODO: Consider using just a single list
                lists=10,  # pgvector readme suggests nrows/1000 as a baseline
                opclasses=["vector_cosine_ops"],
            )
        ]
