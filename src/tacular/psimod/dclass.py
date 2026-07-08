"""``PsimodInfo``: a PSI-MOD ontology entry."""

from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class PsimodInfo(OboEntity):
    """Class to store information about a PSI-MOD modification"""

    @property
    def id_tag(self) -> str:
        """`id` with leading zeros stripped, e.g. ``"00007"`` -> ``"7"``. Same
        behavior as :attr:`OboEntity.id_tag`; PSI-MOD ids have no extra prefix to strip."""
        return self.id.lstrip("0")
