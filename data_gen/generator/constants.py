from enum import StrEnum
from typing import Final

PROTON_MASS: Final[float] = 1.00727646688


class OutputFile(StrEnum):
    AMINO_ACIDS = "../src/tacular/amino_acids/data.py"
    FRAGMENT_IONS = "../src/tacular/ion_types/data.py"
    MONOSACCHARIDES = "../src/tacular/monosaccharides/data.py"
    UNIMOD = "../src/tacular/unimod/data.py"
    PSIMOD = "../src/tacular/psimod/data.py"
    XLMOD = "../src/tacular/xlmod/data.py"
    PROTEASES = "../src/tacular/proteases/data.py"
    REFMOL = "../src/tacular/refmol/data.py"
    NEUTRAL_DELTAS = "../src/tacular/neutral_deltas/data.py"
    RESID = "../src/tacular/resid/data.py"
    GNO = "../src/tacular/gno/data.py"
