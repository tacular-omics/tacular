from ..obo_lookup import OntologyLookup
from .data import UNIPROT_PTM_MODIFICATIONS, VERSION
from .dclass import UniprotPtmInfo


class UniprotPtmLookup(OntologyLookup[UniprotPtmInfo]):
    def __init__(self, data: dict[str, UniprotPtmInfo], version: str) -> None:
        super().__init__(
            data=data,
            ontology_name="UniProt-PTM",
            _version=version,
        )


UNIPROT_PTM_LOOKUP = UniprotPtmLookup(UNIPROT_PTM_MODIFICATIONS, VERSION)
