"""``XlModLookup`` (singleton ``XLMOD_LOOKUP``): id/name/mass lookup over the XLMOD ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import VERSION, XLMOD_MODIFICATIONS
from .dclass import XlModInfo


class XlModLookup(OntologyLookup[XlModInfo]):
    def __init__(self, data: dict[str, XlModInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` bound to the XLMOD ontology (no id prefix to strip)."""
        super().__init__(
            data=data,
            ontology_name="XLMOD",
            _version=version,
        )


XLMOD_LOOKUP = XlModLookup(*resolve("xlmodifications.json", XlModInfo, XLMOD_MODIFICATIONS, VERSION))
