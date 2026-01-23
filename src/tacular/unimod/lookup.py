from ..obo_lookup import OntologyLookup
from .data import UNIMOD_MODIFICATIONS, VERSION
from .dclass import UnimodInfo


class UnimodLookup(OntologyLookup[UnimodInfo]):
    def __init__(self, data: dict[str, UnimodInfo], version: str) -> None:
        super().__init__(
            data=data,
            ontology_name="UNIMOD",
            _version=version,
        )


UNIMOD_LOOKUP = UnimodLookup(UNIMOD_MODIFICATIONS, VERSION)
