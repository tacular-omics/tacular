from ..obo_lookup import OntologyLookup
from .data import VERSION, XLMOD_MODIFICATIONS
from .dclass import XlModInfo


class XlModLookup(OntologyLookup[XlModInfo]):
    def __init__(self, data: dict[str, XlModInfo]) -> None:
        super().__init__(
            data=data,
            ontology_name="XLMOD",
            id_prefixes=("xlmod",),
            name_prefixes=("x",),
            _version=VERSION,
        )


XLMOD_LOOKUP = XlModLookup(XLMOD_MODIFICATIONS)
