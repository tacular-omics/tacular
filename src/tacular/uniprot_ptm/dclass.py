from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class UniprotPtmInfo(OboEntity):
    """Class to store information about a UniProt PTM entry"""

    @property
    def id_tag(self) -> str:
        return self.id.lstrip("0")
