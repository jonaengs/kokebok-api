from pathlib import Path
from typing import Any, Callable

from django.test import TestCase
from parameterized import parameterized_class
from recipes.scraping.tests.base_scraper_test import BaseScraperTest

DOCS_DIR = Path("recipes/scraping/tests/html")


TestParams = dict[str, dict[str, Any]]


def params_generator(parameters: TestParams):
    """
    Returns a generator of the given parameters dict, but with
    "doc" key mapping to the actual document contents.
    Prepends "expected_" to all other keys.
    """
    for doc, expected in parameters.items():
        yield {
            "doc": open(DOCS_DIR / doc, encoding="utf-8").read(),
            "doc_name": doc,
        } | {"expected_" + key: val for key, val in expected.items()}


def name_cls_plus_doc(cls, _idx, params_dict):
    return cls.__name__ + "/" + params_dict["doc_name"]


def inject_base_tests(
    include: list[Callable] | None = None,
    exclude: list[Callable] | None = None,
):
    """
    Injects the methods of BaseScraperTest into the decorated class,
    solving the problem with parameterized (issue #119) ignoring
    inherited test cases.

    include and exclude are lists of methods.
    e.g., include = [BaseScraperTest.test_repeat_calls, ...]
    """
    assert not (include and exclude), ("Choose one", include, exclude)

    base_tests = dict(BaseScraperTest.__dict__)
    if include:
        base_tests = {
            name: val for name, val in base_tests.items() if val in include
        }
    if exclude:
        base_tests = {
            name: val for name, val in base_tests.items() if val not in exclude
        }

    def decorator(cls):
        return type(
            cls.__name__,
            (TestCase,),
            base_tests | dict(cls.__dict__),
        )

    return decorator


def with_params(parameters: dict[str, dict[str, Any]]):
    def decorator(cls):
        parametrized = parameterized_class(
            params_generator(parameters), class_name_func=name_cls_plus_doc
        )
        return parametrized(cls)

    return decorator
