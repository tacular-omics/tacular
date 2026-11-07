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

    **Coverage.** This lookup holds the single-residue modifications of the vocabulary
    that carry a formula, a mass or a composition: 440 of the 750 entries in the bundled
    ``2026_03`` release. Two groups are left out, and the same exclusions apply after
    ``tacular update uniprot_ptm``:

    * the 159 ``CROSSLNK`` entries. Their ``TG`` (target) and ``PP`` (position) values
      describe a link between two residues, not a modification of one residue, so a
      single-residue id/name/mass lookup cannot represent them.
    * 151 further entries (69 ``MOD_RES``, 67 ``CARBOHYD``, 15 ``LIPID``) that give no
      formula, no mass and no composition upstream.

    For the whole vocabulary, crosslinks included, use `uniprotptmpy
    <https://github.com/tacular-omics/uniprotptmpy>`_, which parses ptmlist.txt in full
    and keeps the ``CROSSLNK`` feature type.
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
