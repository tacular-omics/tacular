from ..obo_lookup import OntologyLookup
from .data import RESID_MODIFICATIONS, VERSION
from .dclass import ResidInfo


class ResidLookup(OntologyLookup[ResidInfo]):
    def __init__(self, data: dict[str, ResidInfo], version: str) -> None:
        super().__init__(
            data=data,
            ontology_name="RESID",
            id_prefixes=("resid",),
            name_prefixes=("r",),
            _version=version,
        )


RESID_LOOKUP = ResidLookup(RESID_MODIFICATIONS, VERSION)
