"""``UnimodLookup`` (singleton ``UNIMOD_LOOKUP``): id/name/mass lookup over the UNIMOD ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import UNIMOD_MODIFICATIONS, VERSION
from .dclass import UnimodInfo

__all__ = ["UNIMOD_LOOKUP", "UnimodLookup"]


class UnimodLookup(OntologyLookup[UnimodInfo]):
    """UNIMOD lookup (singleton ``UNIMOD_LOOKUP``).

    Query by ``"Phospho"``, ``"U:Phospho"``, ``"21"``, ``21``, ``"UNIMOD:21"`` or ``"U:21"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises :class:`~tacular.TacularKeyError` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, UnimodInfo], version: str) -> None:
        """Wrap ``data`` (entries keyed by raw id) in an :class:`~tacular.OntologyLookup` for UNIMOD."""
        super().__init__(
            data,
            "UNIMOD",
            version=version,
            accession_prefixes=("UNIMOD:", "U:"),
        )


UNIMOD_LOOKUP = UnimodLookup(*resolve("unimodifications.json", UnimodInfo, UNIMOD_MODIFICATIONS, VERSION))
