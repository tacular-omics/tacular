"""``XlModInfo``: an XLMOD ontology entry."""

from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class XlModInfo(OboEntity):
    """Class to store information about an XLMOD modification"""

    @property
    def id_tag(self) -> str:
        """`id` with leading zeros stripped, e.g. ``"01000"`` -> ``"1000"``. Same
        behavior as :attr:`OboEntity.id_tag`; XLMOD ids have no extra prefix to strip."""
        return self.id.lstrip("0")
