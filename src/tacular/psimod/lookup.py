"""``PsimodLookup`` (singleton ``PSIMOD_LOOKUP``): id/name/mass lookup over the PSI-MOD ontology."""

from .._cache import resolve
from ..obo_lookup import OntologyLookup
from .data import PSI_MODIFICATIONS, VERSION
from .dclass import PsimodInfo


class PsimodLookup(OntologyLookup[PsimodInfo]):
    def __init__(self, data: dict[str, PsimodInfo], version: str) -> None:
        """Wrap `data` in an `OntologyLookup` bound to the PSI-MOD ontology (no id prefix to strip)."""
        super().__init__(
            data=data,
            ontology_name="PSI-MOD",
            _version=version,
        )


PSIMOD_LOOKUP = PsimodLookup(*resolve("psimodifications.json", PsimodInfo, PSI_MODIFICATIONS, VERSION))
