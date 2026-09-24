"""``UniprotPtmLookup`` (singleton ``UNIPROT_PTM_LOOKUP``): id/name/mass lookup over
UniProt's controlled vocabulary of PTMs (ptmlist.txt).
"""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import UNIPROT_PTM_MODIFICATIONS, VERSION
from .dclass import UniprotPtmInfo

__all__ = ["UNIPROT_PTM_LOOKUP", "UniprotPtmLookup"]


class UniprotPtmLookup(OntologyLookup[UniprotPtmInfo]):
    """UniProt-PTM lookup (singleton ``UNIPROT_PTM_LOOKUP``).

    Query by a name, ``"0476"``, ``476`` or ``"PTM-0476"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises :class:`~tacular.TacularKeyError` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, UniprotPtmInfo], version: str) -> None:
        """Wrap ``data`` (entries keyed by raw id) in an :class:`~tacular.OntologyLookup` for UniProt-PTM."""
        super().__init__(
            data,
            "UniProt-PTM",
            version=version,
            accession_prefixes=("PTM-",),
        )


UNIPROT_PTM_LOOKUP = UniprotPtmLookup(
    *resolve("uniprot_ptm_modifications.json", UniprotPtmInfo, UNIPROT_PTM_MODIFICATIONS, VERSION)
)
