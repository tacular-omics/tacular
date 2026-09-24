"""``UnimodLookup`` (singleton ``UNIMOD_LOOKUP``): id/name/mass lookup over the UNIMOD ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import UNIMOD_MODIFICATIONS, VERSION
from .dclass import UnimodInfo


class UnimodLookup(OntologyLookup[UnimodInfo]):
    """UNIMOD lookup (singleton ``UNIMOD_LOOKUP``): query by ``"Phospho"``, ``"21"``, ``21`` or ``"UNIMOD:21"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises ``KeyError`` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, UnimodInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` for UNIMOD, stripping the "UNIMOD:" accession prefix."""
        super().__init__(
            data=data,
            ontology_name="UNIMOD",
            _version=version,
            _accession_prefix="UNIMOD:",
        )


UNIMOD_LOOKUP = UnimodLookup(*resolve("unimodifications.json", UnimodInfo, UNIMOD_MODIFICATIONS, VERSION))
