from dataclasses import dataclass, field

from ..obo_entity import CV, ModEntity


@dataclass(frozen=True, slots=True)
class UnimodInfo(ModEntity):
    """Class to store information about a Unimod modification"""

    cv: CV = field(default=CV.UNIMOD)
