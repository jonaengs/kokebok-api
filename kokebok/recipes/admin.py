from django.contrib import admin

from recipes.models import Ingredient, Recipe, RecipeIngredient


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "created_at"]


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = [
        "name_no",
        "name_en",
        "name_de",
        "name_fr",
        "name_it",
        "is_ubiquitous",
    ]


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = [
        "name_in_recipe",
        "recipe_title",
        "ingredient_names",
        "is_optional",
    ]

    readonly_fields = ["recipe"]

    @admin.display(ordering="recipe__title")
    def recipe_title(self, obj):
        return obj.recipe.title

    @admin.display(ordering="base_ingredient__name_no")
    def ingredient_names(self, obj):
        return repr(obj.base_ingredient)
