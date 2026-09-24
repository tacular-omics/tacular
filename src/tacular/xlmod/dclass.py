"""``XlmodInfo``: an XLMOD ontology entry."""

from dataclasses import dataclass

from ..obo_entity import OboEntity

__all__ = ["XlmodInfo"]


@dataclass(frozen=True, slots=True)
class XlmodInfo(OboEntity):
    """Class to store information about an XLMOD modification"""
