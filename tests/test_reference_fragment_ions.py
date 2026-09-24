"""Fragment ion offsets checked against the mzPAF v1.0.1 specification (HUPO-PSI, May 2026).

Source: https://www.psidev.info/mzPAF, section 4.4.3 "Primary series ions". Every offset
is the neutral composition added to the sum of residues in the fragment; the charge
(``(H+)z`` in the spec) is not part of it. For d, v and w ions the residue sum excludes
the residue whose side chain is cleaved (``Σn-1(AA)``, ``Σc-1(AA)``): the offset is that
residue's backbone remnant plus any side-chain group it keeps.

The spec gives the generic d, v and w formulas. For the amino-acid-specific d and w ions it
describes the retained group ("For Threonine da has an additional group of OH and db a
group of CH3", "For more details and the calculation [of w] see the d ion"): each specific
ion replaces one hydrogen on the beta carbon of the generic remnant with that group.
"""

import pytest

from tacular import ELEMENT_LOOKUP
from tacular.ion_types import IonType
from tacular.ion_types.data import ION_TYPE_DICT

# Neutral offsets, in the spec's convention (charge carriers excluded).
MZPAF_OFFSETS: dict[IonType, dict[str, int]] = {
    IonType.A: {"C": -1, "O": -1},  # Σ(AA) - CO
    IonType.B: {},  # Σ(AA)
    IonType.C: {"N": 1, "H": 3},  # Σ(AA) + NH3
    IonType.X: {"C": 1, "O": 2},  # Σ(AA) + CO2
    IonType.Y: {"H": 2, "O": 1},  # Σ(AA) + H2O
    IonType.Z_RADICAL: {"O": 1, "N": -1},  # mzPAF "z" is z-dot: Σ(AA) + H2O - NH2
    # Σn-1(AA) + C2H4N: remnant -NH-CH=CH2 of the cleaved residue
    IonType.D: {"C": 2, "H": 4, "N": 1},
    IonType.D_VALINE: {"C": 3, "H": 6, "N": 1},  # keeps CH3
    IonType.DA_THREONINE: {"C": 2, "H": 4, "N": 1, "O": 1},  # keeps OH
    IonType.DB_THREONINE: {"C": 3, "H": 6, "N": 1},  # keeps CH3
    IonType.DA_ISOLEUCINE: {"C": 4, "H": 8, "N": 1},  # keeps C2H5
    IonType.DB_ISOLEUCINE: {"C": 3, "H": 6, "N": 1},  # keeps CH3
    # Σc-1(AA) + C2H3NO2: y-type remnant with the whole side chain lost
    IonType.V: {"C": 2, "H": 3, "N": 1, "O": 2},
    # Σc-1(AA) + C3H4O2: z-dot remnant CH(=CH2)-CO- plus the C-terminal OH
    IonType.W: {"C": 3, "H": 4, "O": 2},
    IonType.W_VALINE: {"C": 4, "H": 6, "O": 2},  # keeps CH3
    IonType.WA_THREONINE: {"C": 3, "H": 4, "O": 3},  # keeps OH
    IonType.WB_THREONINE: {"C": 4, "H": 6, "O": 2},  # keeps CH3
    IonType.WA_ISOLEUCINE: {"C": 5, "H": 8, "O": 2},  # keeps C2H5
    IonType.WB_ISOLEUCINE: {"C": 4, "H": 6, "O": 2},  # keeps CH3
}


def _mass(composition: dict[str, int], monoisotopic: bool = True) -> float:
    total = 0.0
    for symbol, count in composition.items():
        info = ELEMENT_LOOKUP[symbol]
        total += (info.mass if monoisotopic else info.average_mass) * count
    return total


@pytest.mark.parametrize("ion_type", list(MZPAF_OFFSETS), ids=str)
def test_offset_composition_matches_mzpaf(ion_type):
    info = ION_TYPE_DICT[ion_type]
    got = {k: v for k, v in (info.dict_composition or {}).items() if v}
    assert got == MZPAF_OFFSETS[ion_type]


@pytest.mark.parametrize("ion_type", list(MZPAF_OFFSETS), ids=str)
def test_offset_mass_matches_mzpaf(ion_type):
    info = ION_TYPE_DICT[ion_type]
    assert info.monoisotopic_mass == pytest.approx(_mass(MZPAF_OFFSETS[ion_type]), abs=1e-6)
    assert info.average_mass == pytest.approx(_mass(MZPAF_OFFSETS[ion_type], False), abs=1e-6)


@pytest.mark.parametrize(("heavier", "lighter"), [("da", "db"), ("wa", "wb")])
@pytest.mark.parametrize("residue", ["threonine", "isoleucine"])
def test_a_variant_is_the_heavier_one(heavier, lighter, residue):
    # mzPAF: "listed as 'daN' and 'dbN' where a is the heaviest of the two options"
    a = ION_TYPE_DICT[IonType(f"{heavier}-{residue}")].monoisotopic_mass
    b = ION_TYPE_DICT[IonType(f"{lighter}-{residue}")].monoisotopic_mass
    assert a is not None and b is not None
    assert a > b


@pytest.mark.parametrize("ion_type", list(ION_TYPE_DICT), ids=str)
def test_every_offset_mass_matches_its_composition(ion_type):
    info = ION_TYPE_DICT[ion_type]
    if info.dict_composition is None or info.monoisotopic_mass is None:
        pytest.skip("no fixed offset (resolved per residue)")
    assert info.monoisotopic_mass == pytest.approx(_mass(dict(info.dict_composition)), abs=1e-6)
    assert info.average_mass == pytest.approx(_mass(dict(info.dict_composition), False), abs=1e-6)
