"""``XlmodLookup`` (singleton ``XLMOD_LOOKUP``): id/name/mass lookup over the XLMOD ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import VERSION, XLMOD_MODIFICATIONS
from .dclass import XlmodInfo

__all__ = ["XLMOD_LOOKUP", "XlmodLookup"]


class XlmodLookup(OntologyLookup[XlmodInfo]):
    """XLMOD lookup (singleton ``XLMOD_LOOKUP``).

    Query by a name, ``"02001"``, ``"XLMOD:02001"`` or ``"X:02001"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises :class:`~tacular.TacularKeyError` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, XlmodInfo], version: str) -> None:
        """Wrap ``data`` (entries keyed by raw id) in an :class:`~tacular.OntologyLookup` for XLMOD."""
        super().__init__(
            data,
            "XLMOD",
            version=version,
            accession_prefixes=("XLMOD:", "X:"),
        )


XLMOD_LOOKUP = XlmodLookup(*resolve("xlmodifications.json", XlmodInfo, XLMOD_MODIFICATIONS, VERSION))
