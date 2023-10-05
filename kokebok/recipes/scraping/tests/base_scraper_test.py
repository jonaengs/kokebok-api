from bs4 import BeautifulSoup


class BaseScraperTest:
    def setUp(self) -> None:
        self.scraper = self.scraper_cls(url=None, html=self.doc)  # type: ignore[attr-defined] # noqa

    def test_repeat_calls(self):
        # Check that return values do not change over repeat calls, for example
        # due to mutation of internal values
        scraper = self.scraper

        ingredient_groups_1 = scraper.ingredient_groups()
        preamble_1 = scraper.preamble()
        content_1 = scraper.content()

        for _ in range(3):
            scraper.ingredient_groups()
            scraper.preamble()
            scraper.content()

        self.assertEqual(scraper.ingredient_groups(), ingredient_groups_1)
        self.assertEqual(scraper.preamble(), preamble_1)
        self.assertEqual(scraper.content(), content_1)

    def test_content_text(self):
        self.maxDiff = None
        content = self.scraper.content()
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
        groups = self.scraper.ingredient_groups()

        self.assertEqual(len(groups.keys()), len(self.expected_group_names))
        for found_name, expected_name in zip(groups, self.expected_group_names):
            self.assertEqual(found_name, expected_name)

    def test_preamble(self):
        self.assertEqual(self.scraper.preamble(), self.expected_preamble)
