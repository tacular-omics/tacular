"""``MonosaccharideInfo``: an OBO entry for a monosaccharide (uses the base class's
numeric ``id_tag``, no ontology-specific override).
"""

from dataclasses import dataclass

from ..obo_entity import OboEntity

__all__ = ["MonosaccharideInfo"]


@dataclass(frozen=True, slots=True)
class MonosaccharideInfo(OboEntity):
    """Class to store information about a monosaccharide"""
