"""``PsimodLookup`` (singleton ``PSIMOD_LOOKUP``): id/name/mass lookup over the PSI-MOD ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import PSI_MODIFICATIONS, VERSION
from .dclass import PsimodInfo

__all__ = ["PSIMOD_LOOKUP", "PsimodLookup"]


class PsimodLookup(OntologyLookup[PsimodInfo]):
    """PSI-MOD lookup (singleton ``PSIMOD_LOOKUP``).

    Query by a name, ``"00046"``, ``46``, ``"MOD:00046"`` or ``"M:00046"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises :class:`~tacular.TacularKeyError` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, PsimodInfo], version: str) -> None:
        """Wrap ``data`` (entries keyed by raw id) in an :class:`~tacular.OntologyLookup` for PSI-MOD."""
        super().__init__(
            data,
            "PSI-MOD",
            version=version,
            accession_prefixes=("MOD:", "M:"),
        )


PSIMOD_LOOKUP = PsimodLookup(*resolve("psimodifications.json", PsimodInfo, PSI_MODIFICATIONS, VERSION))
