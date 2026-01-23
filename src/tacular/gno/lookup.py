from ..obo_lookup import OntologyLookup
from .data import GNO_GLYCANS, VERSION
from .dclass import GnoInfo


class GnoLookup(OntologyLookup[GnoInfo]):
    def __init__(self, data: dict[str, GnoInfo], version: str) -> None:
        super().__init__(
            data=data,
            ontology_name="GNO",
            _version=version,
        )


GNO_LOOKUP = GnoLookup(GNO_GLYCANS, VERSION)
