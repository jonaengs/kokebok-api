import textwrap
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from django.test import TestCase
from parameterized import parameterized_class
from recipes.scraping.scrapers.tineno import TineNoScraper

docs_dir = Path("recipes/scraping/tests/html")


parameters = {
    # https://www.tine.no/oppskrifter/middag-og-hovedretter/pasta-og-ris/urtepasta-med-kylling
    "tineno.kylling_urtepasta.html": {
        "content": "Tips\nSprøstekt bacon smaker også veldig godt i denne pastaretten.",
        "group_names": ["", "Urtesaus", "Tilbehør"],
        "preamble": "Oppskrift på deilig pastarett med kylling og nydelig urtesaus. Urtesausen består av Crème Fraîche, og det du måtte ha stående av friske urter.",
    },
    # https://www.tine.no/oppskrifter/middag-og-hovedretter/kylling-og-fjarkre/rask-kylling-tikka-masala
    "tineno.tikka_masala.html": {
        "content": "Tips\nHvis retten skulle koke litt tørr, er det bare å spe på med litt vann.",
        "group_names": ["Ris", "Tikka masala", "Raita"],
        "preamble": "En god og rask oppskrift på en kylling tikka masala. Dette er en rett med små smakseksplosjoner som sender tankene til India.",
    },
    # https://www.tine.no/oppskrifter/bakst/brod-og-rundstykker/horn-med-kefir-brunost-og-bringeb%C3%A6r
    "tineno.horn_kefir.html": {
        "content": textwrap.dedent(
            """\
            Tips
            I deigen benyttes bakepulver og kefir, to ingredienser som sammen bidrar til godt bakverk. Opplever du at deigen er tung å jobbe med, anbefaler vi å elte den litt ekstra.

            Hornene kan fryses. Hvis de tines 1 time på kjøkkenbenken før du varmer dem på 200 ºC i ca. 5 minutter, vil de smake som nystekt.

            Til denne oppskriften er det fint å bruke opp brunostrester. Ta vare på brunostrestene i fryseren og bruk som naturlig søtning i bakverk, revet over havregrøt eller i vaffelrøren.
            """
        ).strip(),
        "group_names": [""],
        "preamble": "Horn bakt med kefir gir saftig bakverk med egen syrlighet som sammen med naturlig søt brunost og bringebær kanskje kan bli din nye hverdagsfavoritt. Oppskriften gir 24 horn som kan fryses, tines og nytes i en travel hverdag.",
    },
}


def get_parameters():
    for doc, expected in parameters.items():
        yield {
            "doc": open(docs_dir / doc, encoding="utf-8").read(),
            "doc_name": doc,
        } | {"expected_" + key: val for key, val in expected.items()}


def parameterized_name_func(cls, _idx, params_dict):
    return cls.__name__ + "/" + params_dict["doc_name"]


@parameterized_class(get_parameters(), class_name_func=parameterized_name_func)
class TineNoTest(TestCase):
    def setUp(self) -> None:
        self.scraper = TineNoScraper(url=None, html=self.doc)
        return super().setUp()

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

    def test_content_no_html_attributes(self):
        content = self.scraper.content()
        soup = BeautifulSoup(content, "html.parser")
        self.assertEqual(soup.attrs, {})
        for child in soup.children:
            if isinstance(child, Tag):
                self.assertEqual(child.attrs, {})

    def test_group_names(self):
        groups = self.scraper.ingredient_groups()

        self.assertEqual(len(groups.keys()), len(self.expected_group_names))
        for found_name, expected_name in zip(groups, self.expected_group_names):
            self.assertEqual(found_name, expected_name)

    def test_preamble(self):
        self.assertEqual(self.scraper.preamble(), self.expected_preamble)
