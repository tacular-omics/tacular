"""``ResidLookup`` (singleton ``RESID_LOOKUP``): id/name/mass lookup over the RESID
ontology, with ids matched with or without the "AA" prefix.
"""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import RESID_MODIFICATIONS, VERSION
from .dclass import ResidInfo


class ResidLookup(OntologyLookup[ResidInfo]):
    def __init__(self, data: dict[str, ResidInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` bound to the RESID ontology, stripping the "AA" id prefix."""
        super().__init__(
            data=data,
            ontology_name="RESID",
            _version=version,
            _id_prefix="AA",
        )


RESID_LOOKUP = ResidLookup(*resolve("resid_modifications.json", ResidInfo, RESID_MODIFICATIONS, VERSION))
