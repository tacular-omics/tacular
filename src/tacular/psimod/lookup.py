"""``PsimodLookup`` (singleton ``PSIMOD_LOOKUP``): id/name/mass lookup over the PSI-MOD ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import PSI_MODIFICATIONS, VERSION
from .dclass import PsimodInfo


class PsimodLookup(OntologyLookup[PsimodInfo]):
    """PSI-MOD lookup (singleton ``PSIMOD_LOOKUP``): query by a name, ``"00046"``, ``46`` or ``"MOD:00046"``.

    See :class:`~tacular.OntologyLookup` for the full query API. ``lookup[key]``
    raises ``KeyError`` if nothing matches; ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[str, PsimodInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` for PSI-MOD, stripping the "MOD:" accession prefix."""
        super().__init__(
            data=data,
            ontology_name="PSI-MOD",
            _version=version,
            _accession_prefix="MOD:",
        )


PSIMOD_LOOKUP = PsimodLookup(*resolve("psimodifications.json", PsimodInfo, PSI_MODIFICATIONS, VERSION))
