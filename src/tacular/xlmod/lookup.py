"""``XlModLookup`` (singleton ``XLMOD_LOOKUP``): id/name/mass lookup over the XLMOD ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import VERSION, XLMOD_MODIFICATIONS
from .dclass import XlModInfo


class XlModLookup(OntologyLookup[XlModInfo]):
    """XLMOD lookup (singleton ``XLMOD_LOOKUP``): query by a name, ``"01000"`` or ``"XLMOD:01000"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises ``KeyError`` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, XlModInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` for XLMOD, stripping the "XLMOD:" accession prefix."""
        super().__init__(
            data=data,
            ontology_name="XLMOD",
            _version=version,
            _accession_prefix="XLMOD:",
        )


XLMOD_LOOKUP = XlModLookup(*resolve("xlmodifications.json", XlModInfo, XLMOD_MODIFICATIONS, VERSION))
