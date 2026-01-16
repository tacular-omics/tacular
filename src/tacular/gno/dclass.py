from dataclasses import dataclass, field

from ..obo_entity import CV, ModEntity


@dataclass(frozen=True, slots=True)
class GnoInfo(ModEntity):
    """Class to store information about a PSI-MOD modification"""

    cv: CV = field(default=CV.GNOME)
