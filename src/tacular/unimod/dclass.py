"""``UnimodInfo``: a UNIMOD ontology entry."""

from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class UnimodInfo(OboEntity):
    """Class to store information about a Unimod modification"""

    @property
    def id_tag(self) -> str:
        """`id` with leading zeros stripped, e.g. ``"042"`` -> ``"42"``. Same
        behavior as :attr:`OboEntity.id_tag`; UNIMOD ids have no extra prefix to strip."""
        return self.id.lstrip("0")
