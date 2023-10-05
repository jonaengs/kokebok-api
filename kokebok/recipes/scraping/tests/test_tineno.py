import textwrap

from bs4 import BeautifulSoup, Tag
from django.test import TestCase
from recipes.scraping.scrapers.tineno import TineNoScraper
from recipes.scraping.tests._utils import inject_base_tests, with_params

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


@with_params(parameters)
@inject_base_tests()
class TineNoTest(TestCase):
    scraper_cls = TineNoScraper

    def test_content_no_html_attributes(self):
        content = self.scraper.content()
        soup = BeautifulSoup(content, "html.parser")
        self.assertEqual(soup.attrs, {})
        for child in soup.children:
            if isinstance(child, Tag):
                self.assertEqual(child.attrs, {})
