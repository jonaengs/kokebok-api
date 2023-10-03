from ninja import ModelSchema
from recipe_scrapers._abstract import AbstractScraper
from recipes.models import Recipe, RecipeIngredient


class ScraperMixin:
    def __init__(self, url: str, *args, **kwargs):
        existing = Recipe.objects.filter(origin_url=url).exists()
        if existing:
            raise ValueError("URL has already been scraped")
        super(ScraperMixin, self).__init__(url, *args, **kwargs)  # type: ignore


class ScrapedRecipeIngredient(ModelSchema):
    base_ingredient_str: str

    class Config:
        model = RecipeIngredient
        model_exclude = ["base_ingredient", "recipe"]


HTML = str


# TODO: Look into whether we can dynamically set the parent
# of this class to be the recipe_scrapers class for the
# site we're scraping. So for example, TineNoScraper's class
# hierarchy would look like:
# TineNoScraper < MyScraper < TineNo < AbstractScraper
class MyScraper(AbstractScraper):
    def ingredient_groups(  # type: ignore
        self,
    ) -> dict[str, list[ScrapedRecipeIngredient]]:
        ...

    def ingress(self) -> str:  # type: ignore
        ...

    def content(self) -> HTML:  # type: ignore
        ...
