from unittest import mock

from bs4 import BeautifulSoup
from recipes import scraping


class BaseScraperTest:
    def setUp(self) -> None:
        # Make sure we aren't accidentally making any web requests
        def _raise(*args, **kwargs):
            raise Exception("Mocked method called")

        patcher = mock.patch("requests.get", new=_raise)
        self.addCleanup(patcher.stop)  # type: ignore[attr-defined]
        patcher.start()

        # Then setup scraper
        self.scraper = self.scraper_cls(url=self._url, html=self.doc)  # type: ignore[attr-defined] # noqa

    def test_repeat_calls(self):
        # Check that return values do not change over repeat calls, for example
        # due to mutation of internal values
        scraper = self.scraper

        my_ingredient_groups_1 = scraper.my_ingredient_groups()
        preamble_1 = scraper.my_preamble()
        content_1 = scraper.my_content()

        for _ in range(3):
            scraper.my_ingredient_groups()
            scraper.my_preamble()
            scraper.my_content()

        self.assertEqual(scraper.my_ingredient_groups(), my_ingredient_groups_1)
        self.assertEqual(scraper.my_preamble(), preamble_1)
        self.assertEqual(scraper.my_content(), content_1)

    def test_content_not_empty(self):
        self.assertNotEqual(len(self.scraper.my_content()), 0)

    def test_content_text(self):
        self.maxDiff = None
        content = self.scraper.my_content()
        content_text = BeautifulSoup(content, "html.parser").text.strip()
        content_text = "\n".join(line.strip() for line in content_text.split("\n"))
        # Uncomment these lines for debugging test failures
        # print("===================")
        # print(content_text)
        # print(self.expected_content)
        # print("-----------------")
        # print(content_text.encode("utf-8"))
        # print(self.expected_content.encode("utf-8"))
        self.assertEqual(content_text, self.expected_content)

    def test_group_names(self):
        groups = self.scraper.my_ingredient_groups()

        for found_name, expected_name in zip(groups, self.expected_group_names):
            self.assertEqual(found_name, expected_name)

        self.assertEqual(len(groups.keys()), len(self.expected_group_names))

    def test_my_preamble(self):
        self.assertEqual(self.scraper.my_preamble(), self.expected_preamble)

    def test_title(self):
        # title is handled by recipe_scrapers, so this test
        # is mostly just to check that our scraper classes correctly
        # subclass and init so that the underlying scraper
        # methods still work correctly
        self.assertEqual(self.scraper.title(), self.expected_title)

    def test_scraper_function_doesnt_fail(self):
        # Tests more than just the scraper class itself, so
        # consider moving this out to some other test class
        scraped_recipe = scraping.scrape(self._url, self.doc)
        scraped_recipe.clean()
