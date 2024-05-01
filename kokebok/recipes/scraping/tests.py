from pathlib import Path

from django.test import TestCase

from recipes.scraping import scrape

DOCS_DIR = Path("recipes/scraping/scraper_tests/html")

hosts_map = {
    "thewoksoflife": "thewoksoflife.com",
    "tineno": "tine.no",
}


class ScrapeTest(TestCase):
    def test_scrape(self):
        """Mainly just tests that the scrape function runs without errors."""

        for doc in DOCS_DIR.iterdir():
            with open(doc, encoding="utf-8") as f:
                html = f.read()

            scrape(url=None, html=html, host=hosts_map[doc.stem.split(".")[0]])
