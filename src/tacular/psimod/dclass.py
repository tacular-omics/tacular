from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class PsimodInfo(OboEntity):
    """Class to store information about a PSI-MOD modification"""

    @property
    def id_tag(self) -> str:
        return self.id.lstrip("0")
