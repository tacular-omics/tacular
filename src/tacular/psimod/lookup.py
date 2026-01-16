from ..obo_lookup import OntologyLookup
from .data import PSI_MODIFICATIONS, VERSION
from .dclass import PsimodInfo


class PsimodLookup(OntologyLookup[PsimodInfo]):
    def __init__(self, data: dict[str, PsimodInfo]) -> None:
        super().__init__(
            data=data,
            ontology_name="PSI-MOD",
            id_prefixes=("mod", "psi-mod"),
            name_prefixes=("m",),
            _version=VERSION,
        )


PSIMOD_LOOKUP = PsimodLookup(PSI_MODIFICATIONS)
