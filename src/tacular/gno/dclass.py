"""``GnoInfo``: a GNOme glycan entry. ``id_tag`` strips the leading "G" used by GNOme ids."""

from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class GnoInfo(OboEntity):
    """Class to store information about a PSI-MOD modification"""

    @property
    def id_tag(self) -> str:
        """`id` with a leading "G" (if present) and then leading zeros stripped,
        e.g. ``"G00008BG"`` -> ``"8BG"``."""
        if self.id.startswith("G"):
            return self.id[1:].lstrip("0")
        return self.id.lstrip("0")
