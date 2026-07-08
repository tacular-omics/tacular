"""Periodic-table and isotope data: re-exports ``ElementInfo``, the ``ELEMENT_LOOKUP``
singleton, and ``parse_composition`` for resolving composition dicts to ``ElementInfo`` keys.
"""

from .data import Element
from .dclass import ElementInfo
from .lookup import ELEMENT_LOOKUP, ElementLookup, parse_composition

__all__ = [
    "ElementInfo",
    "Element",
    "ElementLookup",
    "ELEMENT_LOOKUP",
    "parse_composition",
]
