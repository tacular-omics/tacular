"""``GnoLookup`` (singleton ``GNO_LOOKUP``): id/name/mass lookup over the GNO ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import GNO_GLYCANS, VERSION
from .dclass import GnoInfo


class GnoLookup(OntologyLookup[GnoInfo]):
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
