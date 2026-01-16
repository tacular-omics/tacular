from dataclasses import dataclass, field

from ..obo_entity import CV, ModEntity


@dataclass(frozen=True, slots=True)
class ResidInfo(ModEntity):
    """Class to store information about a RESID modification"""

    cv: CV = field(default=CV.RESID)
