"""``ResidInfo``: a RESID ontology entry. ``id_tag`` strips the "AA" prefix used by RESID ids."""

from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class ResidInfo(OboEntity):
    """Class to store information about a RESID modification"""

    @property
    def id_tag(self) -> str:
        """`id` with a leading "AA" prefix (if present) and leading zeros stripped,
        e.g. ``"AA0002"`` -> ``"2"``."""
        if self.id.startswith("AA"):
            return self.id[2:].lstrip("0")
        return self.id.lstrip("0")
