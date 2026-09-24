"""``GnoLookup`` (singleton ``GNO_LOOKUP``): id/name/mass lookup over the GNOme glycan ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import GNO_GLYCANS, VERSION
from .dclass import GnoInfo

__all__ = ["GNO_LOOKUP", "GnoLookup"]


class GnoLookup(OntologyLookup[GnoInfo]):
    """GNO lookup (singleton ``GNO_LOOKUP``).

    Query by a name, ``"G00008BG"``, ``"GNO:G00008BG"`` or ``"G:G00008BG"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises :class:`~tacular.TacularKeyError` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, GnoInfo], version: str) -> None:
        """Wrap ``data`` (entries keyed by raw id) in an :class:`~tacular.OntologyLookup` for GNO."""
        super().__init__(
            data,
            "GNO",
            version=version,
            accession_prefixes=("GNO:", "G:"),
            id_prefix="G",
        )


GNO_LOOKUP = GnoLookup(*resolve("gnome_modifications.json", GnoInfo, GNO_GLYCANS, VERSION))
