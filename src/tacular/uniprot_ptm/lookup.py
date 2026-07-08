"""``UniprotPtmLookup`` (singleton ``UNIPROT_PTM_LOOKUP``): id/name/mass lookup over UniProt's PTM list."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import UNIPROT_PTM_MODIFICATIONS, VERSION
from .dclass import UniprotPtmInfo


class UniprotPtmLookup(OntologyLookup[UniprotPtmInfo]):
    def __init__(self, data: dict[str, UniprotPtmInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` bound to the UniProt-PTM ontology (no id prefix to strip)."""
        super().__init__(
            data=data,
            ontology_name="UniProt-PTM",
            _version=version,
        )


UNIPROT_PTM_LOOKUP = UniprotPtmLookup(
    *resolve("uniprot_ptm_modifications.json", UniprotPtmInfo, UNIPROT_PTM_MODIFICATIONS, VERSION)
)
