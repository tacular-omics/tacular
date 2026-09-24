"""``UnimodInfo``: a UNIMOD ontology entry."""

from dataclasses import dataclass

from ..obo_entity import OboEntity

__all__ = ["UnimodInfo"]


@dataclass(frozen=True, slots=True)
class UnimodInfo(OboEntity):
    """Class to store information about a Unimod modification"""
