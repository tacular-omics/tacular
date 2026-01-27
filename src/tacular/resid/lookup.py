from ..obo_lookup import OntologyLookup
from .data import RESID_MODIFICATIONS, VERSION
from .dclass import ResidInfo


class ResidLookup(OntologyLookup[ResidInfo]):
    def __init__(self, data: dict[str, ResidInfo], version: str) -> None:
        super().__init__(
            data=data,
            ontology_name="RESID",
            _version=version,
            _id_prefix="AA",
        )


RESID_LOOKUP = ResidLookup(RESID_MODIFICATIONS, VERSION)
