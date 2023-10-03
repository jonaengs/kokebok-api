import requests
from recipes.scraping import get_scraper

url = "https://www.tine.no/oppskrifter/middag-og-hovedretter/pasta-og-ris/urtepasta-med-kylling"  # noqa
# url = "https://www.tine.no/oppskrifter/middag-og-hovedretter/kylling-og-fjarkre/rask-kylling-tikka-masala"  # noqa
# url = "https://thewoksoflife.com/red-curry-chicken/"
response = requests.get(url)
with open("recipes/scraping/page.html", encoding="utf-8", mode="w") as out:
    out.write(response.content.decode("utf-8"))


with open("recipes/scraping/page.html", encoding="utf-8") as f:
    page_raw = f.read()

scraper = get_scraper(url, html=page_raw).scraper
print("------------")
print(scraper.title())
print("------------")
print(scraper.ingress())
print("------------")
print(scraper.ingredient_groups())
print("------------")
print(scraper.content())
print("------------")
