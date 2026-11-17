"""parse_formula and formula_mass: formula strings to compositions and masses (#60)."""

import pytest

import tacular as t
from tacular import ELEMENT_LOOKUP, TacularError, formula_mass, parse_composition, parse_formula

GLUCOSE_MONO = 180.06338810418


def test_plain_formula_matches_parse_composition_shape():
    parsed = parse_formula("C6H12O6")
    assert parsed == parse_composition({"C": 6, "H": 12, "O": 6})
    assert all(isinstance(k, t.ElementInfo) for k in parsed)
    assert parsed[ELEMENT_LOOKUP["C"]] == 6


def test_monoisotopic_mass_of_glucose():
    assert formula_mass("C6H12O6") == pytest.approx(GLUCOSE_MONO, abs=1e-9)
    assert formula_mass("C6H12O6", monoisotopic=True) == formula_mass("C6H12O6")


def test_average_mass_differs_and_uses_average_masses():
    expected = 6 * ELEMENT_LOOKUP["C"].average_mass + 12 * ELEMENT_LOOKUP["H"].average_mass
    expected += 6 * ELEMENT_LOOKUP["O"].average_mass
    assert formula_mass("C6H12O6", monoisotopic=False) == pytest.approx(expected)
    assert formula_mass("C6H12O6", monoisotopic=False) > formula_mass("C6H12O6")


def test_proforma_isotope_resolves_through_element_lookup():
    parsed = parse_formula("[13C6]H12O6")
    assert parsed[ELEMENT_LOOKUP["13C"]] == 6
    assert ELEMENT_LOOKUP["C"] not in parsed
    delta = formula_mass("[13C6]H12O6") - formula_mass("C6H12O6")
    assert delta == pytest.approx(6 * (ELEMENT_LOOKUP["13C"].mass - 12.0))


def test_mixed_isotope_and_element_groups():
    parsed = parse_formula("C[13C5]H12O6")
    assert parsed[ELEMENT_LOOKUP["C"]] == 1
    assert parsed[ELEMENT_LOOKUP["13C"]] == 5


def test_negative_and_repeated_counts_follow_the_private_parser():
    assert parse_formula("C6H-2") == parse_composition({"C": 6, "H": -2})
    assert parse_formula("CH2C") == parse_composition({"C": 2, "H": 2})
    assert parse_formula("C-6[13C6]") == parse_composition({"C": -6, "13C": 6})


def test_count_of_one_is_implicit():
    assert parse_formula("H2O") == parse_composition({"H": 2, "O": 1})


@pytest.mark.parametrize(
    "bad",
    [
        "13C6H12O6",
        "H(2)C(6)",
        "",
        "   ",
        "Xx2",
        "[13Xx6]",
        "[99C]",
        "C6H12O6!",
        "c6h12o6",
        "[C6]",
        "[13C6",
        "C6 -",
        "C²",
    ],
)
def test_bad_input_raises_tacular_error_naming_the_text(bad):
    with pytest.raises(TacularError) as exc:
        parse_formula(bad)
    assert repr(bad) in str(exc.value)
    with pytest.raises(TacularError):
        formula_mass(bad)


@pytest.mark.parametrize(
    "bad",
    [
        "C6 H12 O6",
        " C6H12O6",
        "C6H12O6 ",
        "C6\tH12O6",
        "C6H12\nO6",
        "[13C6] H12O6",
    ],
)
def test_whitespace_anywhere_raises_rather_than_parsing(bad):
    """A formula is one token: whitespace is never skipped, so there is one dialect."""
    with pytest.raises(TacularError, match="whitespace") as exc:
        parse_formula(bad)
    assert repr(bad) in str(exc.value)
    with pytest.raises(TacularError, match="whitespace"):
        formula_mass(bad)


def test_bare_isotope_spelling_error_points_to_bracket_spelling():
    with pytest.raises(TacularError, match=r"13C6H12O6.*\[13C6\]H12O6"):
        parse_formula("13C6H12O6")


@pytest.mark.parametrize("bad", [None, 6, b"C6", ["C6"], {"C": 6}])
def test_non_string_raises_tacular_error(bad):
    with pytest.raises(TacularError, match="formula string"):
        parse_formula(bad)  # ty: ignore[invalid-argument-type]


def test_monoisotopic_is_keyword_only():
    """Every option in tacular is keyword-only, so a positional flag is a TypeError."""
    with pytest.raises(TypeError):
        formula_mass("H2O", False)  # ty: ignore[too-many-positional-arguments]
    assert formula_mass("H2O", monoisotopic=False) > formula_mass("H2O", monoisotopic=True)


def test_public_exports():
    assert "parse_formula" in t.__all__ and "formula_mass" in t.__all__
    assert t.parse_formula is parse_formula and t.formula_mass is formula_mass


def test_parse_composition_still_refuses_a_string():
    with pytest.raises(TacularError):
        parse_composition("C6H12O6")  # ty: ignore[invalid-argument-type]
