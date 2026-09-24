"""``ResidLookup`` (singleton ``RESID_LOOKUP``): id/name/mass lookup over the RESID ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import RESID_MODIFICATIONS, VERSION
from .dclass import ResidInfo

__all__ = ["RESID_LOOKUP", "ResidLookup"]


class ResidLookup(OntologyLookup[ResidInfo]):
    """RESID lookup (singleton ``RESID_LOOKUP``).

    Query by a name, ``"AA0002"``, ``"2"``, ``2``, ``"RESID:AA0002"`` or ``"R:AA0002"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises :class:`~tacular.TacularKeyError` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, ResidInfo], version: str) -> None:
        """Wrap ``data`` (entries keyed by raw id) in an :class:`~tacular.OntologyLookup` for RESID."""
        super().__init__(
            data,
            "RESID",
            version=version,
            accession_prefixes=("RESID:", "R:"),
            id_prefix="AA",
        )


RESID_LOOKUP = ResidLookup(*resolve("resid_modifications.json", ResidInfo, RESID_MODIFICATIONS, VERSION))
