from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class ResidInfo(OboEntity):
    """Class to store information about a RESID modification"""

    @property
    def id_tag(self) -> str:
        if self.id.startswith("AA"):
            return self.id[2:].lstrip("0")
        return self.id.lstrip("0")
