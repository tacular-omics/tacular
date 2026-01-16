from ..obo_lookup import OntologyLookup
from .data import RESID_MODIFICATIONS, VERSION
from .dclass import ResidInfo


class ResidLookup(OntologyLookup[ResidInfo]):
    def __init__(self, data: dict[str, ResidInfo]) -> None:
        super().__init__(
            data=data,
            ontology_name="RESID",
            id_prefixes=("resid",),
            name_prefixes=("r",),
            _version=VERSION,
        )


RESID_LOOKUP = ResidLookup(RESID_MODIFICATIONS)
