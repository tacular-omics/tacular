"""``UnimodLookup`` (singleton ``UNIMOD_LOOKUP``): id/name/mass lookup over the UNIMOD ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import UNIMOD_MODIFICATIONS, VERSION
from .dclass import UnimodInfo


class UnimodLookup(OntologyLookup[UnimodInfo]):
    def __init__(self, data: dict[str, UnimodInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` bound to the UNIMOD ontology (no id prefix to strip)."""
        super().__init__(
            data=data,
            ontology_name="UNIMOD",
            _version=version,
        )


UNIMOD_LOOKUP = UnimodLookup(*resolve("unimodifications.json", UnimodInfo, UNIMOD_MODIFICATIONS, VERSION))
