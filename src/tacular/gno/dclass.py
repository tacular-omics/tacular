from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class GnoInfo(OboEntity):
    """Class to store information about a PSI-MOD modification"""

    pass
