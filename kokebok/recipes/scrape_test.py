import requests
from recipes.models import Recipe
from recipes.scraping import get_scraper

# url = "https://www.tine.no/oppskrifter/middag-og-hovedretter/pasta-og-ris/urtepasta-med-kylling"  # noqa
# url = "https://www.tine.no/oppskrifter/middag-og-hovedretter/kylling-og-fjarkre/rask-kylling-tikka-masala"  # noqa
url = "https://www.tine.no/oppskrifter/bakst/brod-og-rundstykker/horn-med-kefir-brunost-og-bringeb%C3%A6r"  # noqa
# url = "https://thewoksoflife.com/red-curry-chicken/"
response = requests.get(url)
with open("recipes/scraping/page.html", encoding="utf-8", mode="w") as out:
    out.write(response.content.decode("utf-8"))


with open("recipes/scraping/page.html", encoding="utf-8") as f:
    page_raw = f.read()


def do_scrape(url, html=None):
    existing = Recipe.objects.filter(origin_url=url).exists()
    if existing:
        raise ValueError("URL has already been scraped")

    scraper = get_scraper(url, html=html).scraper
    print("SCRAPE RESULT:\n=============")
    print(
        scraper.title(),
        scraper.preamble(),
        scraper.ingredient_groups(),
        scraper.instructions(),
        scraper.content(),
        sep="\n-------------\n",
    )


do_scrape(url, page_raw)
