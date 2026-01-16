import pytest

from tacular.elements import ELEMENT_LOOKUP, parse_composition


def test_element_lookup_get():
    # Regular element (monoisotopic default)
    c = ELEMENT_LOOKUP["C"]
    assert c.symbol == "C"
    assert c.mass_number is None  # C maps to element entry, not specific isotope
    # Actually, if mass_number is None in key, it returns the most abundant isotope?
    # The docstring says: "('C', None) -> Most abundant carbon isotope (monoisotopic)"

    # Isotope string
    c13 = ELEMENT_LOOKUP["13C"]
    assert c13.symbol == "C"
    assert c13.mass_number == 13

    # Isotope Tuple
    c13_tup = ELEMENT_LOOKUP[("C", 13)]
    assert c13_tup == c13

    # Deuterium
    d = ELEMENT_LOOKUP["D"]
    assert d.symbol == "H"
    assert d.mass_number == 2

    # Errors
    with pytest.raises(KeyError):
        ELEMENT_LOOKUP["Zzz"]
    with pytest.raises(ValueError):
        ELEMENT_LOOKUP["123"]  # No symbol


def test_element_mass():
    # Monoisotopic vs Average
    # C monoisotopic is 12.0
    # C average is ~12.011

    m_mono = ELEMENT_LOOKUP.mass("C", monoisotopic=True)
    m_avg = ELEMENT_LOOKUP.mass("C", monoisotopic=False)

    assert m_mono == pytest.approx(12.0, abs=0.001)
    # Average should be different
    assert m_mono != m_avg
    assert m_avg > 12.0

    # Specific isotope mass ignores monoisotopic flag
    m13 = ELEMENT_LOOKUP.mass("13C")
    m13_false = ELEMENT_LOOKUP.mass("13C", monoisotopic=False)
    assert m13 == m13_false
    assert m13 > 13.0


def test_parse_composition():
    comp = {"C": 2, "H": 4, "13C": 1}
    parsed = parse_composition(comp)

    # Check keys are ElementInfo
    keys = list(parsed.keys())
    assert all(hasattr(k, "symbol") for k in keys)

    # Verify mapping
    c_info = ELEMENT_LOOKUP["C"]
    h_info = ELEMENT_LOOKUP["H"]
    c13_info = ELEMENT_LOOKUP["13C"]

    assert parsed[c_info] == 2
    assert parsed[h_info] == 4
    assert parsed[c13_info] == 1
