"""Every bundled ontology entry's ``formula`` string must parse back to its own composition.

Reads the bundled ``data.py`` modules directly, so a refreshed user cache cannot mask a
bad snapshot.
"""

import pytest

from tacular._datagen._utils import parse_formula_to_dict
from tacular.gno.data import GNO_GLYCANS
from tacular.psimod.data import PSI_MODIFICATIONS
from tacular.resid.data import RESID_MODIFICATIONS
from tacular.unimod.data import UNIMOD_MODIFICATIONS
from tacular.uniprot_ptm.data import UNIPROT_PTM_MODIFICATIONS
from tacular.xlmod.data import XLMOD_MODIFICATIONS

BUNDLED = {
    "unimod": UNIMOD_MODIFICATIONS,
    "xlmod": XLMOD_MODIFICATIONS,
    "psimod": PSI_MODIFICATIONS,
    "resid": RESID_MODIFICATIONS,
    "gno": GNO_GLYCANS,
    "uniprot_ptm": UNIPROT_PTM_MODIFICATIONS,
}


@pytest.mark.parametrize("name", list(BUNDLED))
def test_formula_parses_to_composition(name):
    data = BUNDLED[name]
    assert data, f"{name} bundled data is empty"
    mismatches = {}
    for key, info in data.items():
        if info.formula is None or info.dict_composition is None:
            continue
        try:
            parsed = parse_formula_to_dict(info.formula)
        except ValueError as e:
            mismatches[key] = (info.formula, f"{type(e).__name__}: {e}")
            continue
        if parsed != dict(info.dict_composition):
            mismatches[key] = (info.formula, parsed, dict(info.dict_composition))
    assert not mismatches, f"{len(mismatches)} {name} formulas do not round-trip, e.g. {list(mismatches.items())[:5]}"
