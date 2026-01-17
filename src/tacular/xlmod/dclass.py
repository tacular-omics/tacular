from dataclasses import dataclass

from ..obo_entity import OboEntity


@dataclass(frozen=True, slots=True)
class XlModInfo(OboEntity):
    """Class to store information about a Unimod modification"""

    pass
