"""``PsimodInfo``: a PSI-MOD ontology entry."""

from dataclasses import dataclass

from ..obo_entity import OboEntity

__all__ = ["PsimodInfo"]


@dataclass(frozen=True, slots=True)
class PsimodInfo(OboEntity):
    """Class to store information about a PSI-MOD modification"""
