from ..obo_lookup import OntologyLookup
from .data import VERSION, XLMOD_MODIFICATIONS
from .dclass import XlModInfo


class XlModLookup(OntologyLookup[XlModInfo]):
    def __init__(self, data: dict[str, XlModInfo], version: str) -> None:
        super().__init__(
            data=data,
            ontology_name="XLMOD",
            _version=version,
        )


XLMOD_LOOKUP = XlModLookup(XLMOD_MODIFICATIONS, VERSION)
