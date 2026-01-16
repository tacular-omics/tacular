from ..obo_lookup import OntologyLookup
from .data import UNIMOD_MODIFICATIONS, VERSION
from .dclass import UnimodInfo


class UnimodLookup(OntologyLookup[UnimodInfo]):
    def __init__(self, data: dict[str, UnimodInfo]) -> None:
        super().__init__(
            data=data,
            ontology_name="UNIMOD",
            id_prefixes=("unimod",),
            name_prefixes=("u",),
            _version=VERSION,
        )


UNIMOD_LOOKUP = UnimodLookup(UNIMOD_MODIFICATIONS)
