from dataclasses import dataclass, field

from ..obo_entity import CV, ModEntity


@dataclass(frozen=True, slots=True)
class XlModInfo(ModEntity):
    """Class to store information about a Unimod modification"""

    cv: CV = field(default=CV.XL_MOD)
