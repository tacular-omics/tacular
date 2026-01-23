import pytest

from tacular.elements import ELEMENT_LOOKUP


@pytest.fixture(autouse=True)
def add_lookup(doctest_namespace):
    doctest_namespace["lookup"] = ELEMENT_LOOKUP
