import requests
from recipe_scrapers import scrape_me

from recipes.models import Recipe
from recipes.scraping.main import get_scraper
from recipes.scraping.utils import RecipeScraperWrapper


def old():
    # url = "https://www.tine.no/oppskrifter/middag-og-hovedretter/pasta-og-ris/urtepasta-med-kylling"  # noqa
    # url = "https://www.tine.no/oppskrifter/middag-og-hovedretter/kylling-og-fjarkre/rask-kylling-tikka-masala"  # noqa
    # url = "https://www.tine.no/oppskrifter/bakst/brod-og-rundstykker/horn-med-kefir-brunost-og-bringeb%C3%A6r"  # noqa
    # url = "https://thewoksoflife.com/red-curry-chicken/"
    # url = "https://thewoksoflife.com/pork-belly-pickled-mustard-greens-chinese/#recipe"
    url = "https://thewoksoflife.com/chicken-katsu-curry-rice/#recipe"
    response = requests.get(url)
    with open("recipes/scraping/page.html", encoding="utf-8", mode="w") as out:
        out.write(response.content.decode("utf-8"))

    with open("recipes/scraping/page.html", encoding="utf-8") as f:
        page_raw = f.read()

    def do_scrape(url, html=None):
        existing = Recipe.objects.filter(origin_url=url).exists()
        if existing:
            raise ValueError("URL has already been scraped")

        registry_result = get_scraper(url, html=html)
        print(registry_result)
        scraper = registry_result.scraper
        print("SCRAPE RESULT:\n=============")
        print(
            scraper.title(),
            scraper.my_preamble(),
            # scraper.description(),
            scraper.my_content(),
            # scraper.ingredients(),
            scraper.my_ingredient_groups(),
            # scraper.instructions(),
            sep="\n-------------\n",
        )

    do_scrape(url, page_raw)


scraper = scrape_me("https://www.feastingathome.com/tomato-risotto/", wild_mode=True)
w = RecipeScraperWrapper(scraper)

print(w.all_text())
