"""``GnoLookup`` (singleton ``GNO_LOOKUP``): id/name/mass lookup over the GNO ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import GNO_GLYCANS, VERSION
from .dclass import GnoInfo


class GnoLookup(OntologyLookup[GnoInfo]):
    """GNOme lookup (singleton ``GNO_LOOKUP``): query by a name, ``"G00008BG"`` or ``"GNO:G00008BG"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises ``KeyError`` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, GnoInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` for GNO, stripping the "GNO:" accession and "G" id prefixes."""
        super().__init__(
            data=data,
            ontology_name="GNO",
            _version=version,
            _accession_prefix="GNO:",
            _id_prefix="G",
        )


GNO_LOOKUP = GnoLookup(*resolve("gnome_modifications.json", GnoInfo, GNO_GLYCANS, VERSION))
