from functools import lru_cache, wraps
from types import FunctionType
from typing import Any, Iterable

import bs4
import pypandoc
from recipe_scrapers._abstract import AbstractScraper


def html_to_markdown(html: str) -> str:
    """
    Convert html to markdown.
    """

    return pypandoc.convert_text(
        html,
        "gfm",
        format="html-native_divs-native_spans",
        sandbox=True,
        extra_args=["--wrap=none"],
    )


def recursive_strip_attrs(tag: bs4.Tag, *whitelist: str) -> bs4.Tag:
    def strip_attrs(tag: bs4.Tag, whitelist: Iterable[str]) -> bs4.Tag:
        for attr in list(tag.attrs.keys()):
            if attr not in whitelist:
                del tag[attr]
        return tag

    strip_attrs(tag, whitelist)
    for child in tag.descendants:
        if isinstance(child, bs4.Tag):
            strip_attrs(child, whitelist)

    return tag


def _not_impl_exc_silencer(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except NotImplementedError:
            return None

    return wrapper


class RecipeScraperWrapperMeta(type):
    def __new__(meta, classname, bases, classDict):
        newClassDict = {}
        for attributeName, attribute in classDict.items():
            if isinstance(attribute, FunctionType):
                # replace it with a wrapped version
                attribute = _not_impl_exc_silencer(attribute)
            newClassDict[attributeName] = attribute
        return type.__new__(meta, classname, bases, newClassDict)


class RecipeScraperWrapper(AbstractScraper):
    """
    Because the recipe_scrapers library has some weird design choices, we wrap their scrapers in this class
    to make interfacing with them easier.

    This class also implements an additional method:
    .all_text()  which attempts to return all the text describing the recipe, converted from html into markdown
    """

    __metaclass__ = RecipeScraperWrapperMeta

    def __init__(self, scraper: AbstractScraper):
        # Make sure we don't set the wrapped scraper to an attribute already in use
        assert not hasattr(scraper, "_scraper")
        self._scraper = scraper

    def __getattribute__(self, name: str) -> Any:
        """Try passing attribute requests to the wrapped scraper"""
        scraper = super().__getattribute__("_scraper")
        if hasattr(scraper, name):
            return getattr(scraper, name)
        return super().__getattribute__(name)

    @lru_cache(maxsize=1)
    def all_text(self) -> str | None:
        article = self._scraper.soup.select("article")
        if article:
            tag = recursive_strip_attrs(article[0], "href", "src")
            return html_to_markdown(str(tag))

        return self._scraper.description()
        # json_ld_extract = extruct.extract(self._scraper.page_data, syntaxes=["json-ld"])
        # json_ld_data = json_ld_extract["json-ld"][0]
        # json_ld_data.get("description", None)
