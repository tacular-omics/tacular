"""``ResidLookup`` (singleton ``RESID_LOOKUP``): id/name/mass lookup over the RESID
ontology, with ids matched with or without the "AA" prefix.
"""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import RESID_MODIFICATIONS, VERSION
from .dclass import ResidInfo


class ResidLookup(OntologyLookup[ResidInfo]):
    """RESID lookup (singleton ``RESID_LOOKUP``): query by a name, ``"AA0002"``, ``"2"`` or ``"RESID:AA0002"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises ``KeyError`` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, ResidInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` for RESID, stripping the "RESID:" and "AA" prefixes."""
        super().__init__(
            data=data,
            ontology_name="RESID",
            _version=version,
            _accession_prefix="RESID:",
            _id_prefix="AA",
        )


RESID_LOOKUP = ResidLookup(*resolve("resid_modifications.json", ResidInfo, RESID_MODIFICATIONS, VERSION))
