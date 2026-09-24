"""Property-based tests (hypothesis) for formula round-trips and lookup key normalisation."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tacular import (
    ELEMENT_LOOKUP,
    GNO_LOOKUP,
    PSIMOD_LOOKUP,
    RESID_LOOKUP,
    UNIMOD_LOOKUP,
    UNIPROT_PTM_LOOKUP,
    XLMOD_LOOKUP,
    Element,
    TacularKeyError,
)
from tacular._datagen._utils import calculate_mass, format_composition_string, parse_formula_to_dict

settings.register_profile("default", max_examples=100, deadline=None)
settings.load_profile("default")

ISOTOPES = sorted((str(sym), a) for sym, a in ELEMENT_LOOKUP.keys() if a is not None)
ELEMENT_KEYS = st.one_of(
    st.sampled_from(sorted(str(e) for e in Element)),
    st.sampled_from([f"{a}{sym}" for sym, a in ISOTOPES]),
)
COMPOSITIONS = st.dictionaries(ELEMENT_KEYS, st.integers(-60, 60), max_size=8)


# --- formulas ---------------------------------------------------------------------------


@given(COMPOSITIONS)
def test_format_then_parse_is_identity(composition):
    assert parse_formula_to_dict(format_composition_string(composition)) == composition


@given(COMPOSITIONS)
def test_formula_string_is_canonical(composition):
    formula = format_composition_string(composition)
    assert format_composition_string(parse_formula_to_dict(formula)) == formula


@given(COMPOSITIONS)
def test_formula_mass_equals_composition_mass(composition):
    mass = calculate_mass(parse_formula_to_dict(format_composition_string(composition)))
    assert mass == pytest.approx(calculate_mass(composition), abs=1e-9)


@pytest.mark.parametrize(
    ("formula", "expected"),
    [
        ("C-6[13C6]", {"C": -6, "13C": 6}),
        ("[13C6][15N2]", {"13C": 6, "15N": 2}),
        ("[2H-3]H3", {"2H": -3, "H": 3}),
        ("C2H-1", {"C": 2, "H": -1}),
        ("HgH", {"Hg": 1, "H": 1}),
    ],
)
def test_isotope_formula_examples(formula, expected):
    assert parse_formula_to_dict(formula) == expected
    assert parse_formula_to_dict(format_composition_string(expected)) == expected


# --- element keys -----------------------------------------------------------------------


@given(st.sampled_from(ISOTOPES))
def test_isotope_string_key_matches_tuple_key(isotope):
    symbol, mass_number = isotope
    key = f"{mass_number}{symbol}"
    assert ELEMENT_LOOKUP[key] is ELEMENT_LOOKUP[(symbol, mass_number)]
    assert key in ELEMENT_LOOKUP


@given(st.sampled_from(ISOTOPES), st.integers(1, 2))
def test_isotope_string_key_rejects_leading_zeros(isotope, zeros):
    symbol, mass_number = isotope
    key = f"{'0' * zeros}{mass_number}{symbol}"
    assert key not in ELEMENT_LOOKUP
    with pytest.raises(TacularKeyError, match="leading zero"):
        ELEMENT_LOOKUP[key]


def test_deuterium_and_tritium_aliases():
    assert ELEMENT_LOOKUP["D"] is ELEMENT_LOOKUP["2H"] is ELEMENT_LOOKUP[("H", 2)]
    assert ELEMENT_LOOKUP["T"] is ELEMENT_LOOKUP["3H"]


# --- ontology id keys -------------------------------------------------------------------

# (lookup, accession prefix, id prefix)
ONTOLOGY_CASES = {
    "unimod": (UNIMOD_LOOKUP, "UNIMOD:", ""),
    "psimod": (PSIMOD_LOOKUP, "MOD:", ""),
    "resid": (RESID_LOOKUP, "RESID:", "AA"),
    "xlmod": (XLMOD_LOOKUP, "XLMOD:", ""),
    "uniprot_ptm": (UNIPROT_PTM_LOOKUP, "PTM-", ""),
    "gno": (GNO_LOOKUP, "GNO:", "G"),
}


def _random_case(draw, text):
    flips = draw(st.lists(st.booleans(), min_size=len(text), max_size=len(text)))
    return "".join(c.swapcase() if f else c for c, f in zip(text, flips, strict=True))


@st.composite
def id_variants(draw, name):
    lookup, accession, id_prefix = ONTOLOGY_CASES[name]
    info = draw(st.sampled_from(lookup.values()))
    bare = info.id.removeprefix(id_prefix)
    body = draw(st.sampled_from([bare, bare.lstrip("0") or "0", "00" + bare]))
    key = id_prefix + body
    if draw(st.booleans()):
        key = accession + key
    return info, _random_case(draw, key)


@pytest.mark.parametrize("name", list(ONTOLOGY_CASES))
@settings(max_examples=50)
@given(data=st.data())
def test_id_key_variants_resolve_to_the_same_entry(name, data):
    info, key = data.draw(id_variants(name))
    assert ONTOLOGY_CASES[name][0].query_id(key) is info
    if info.id.isdigit():
        assert ONTOLOGY_CASES[name][0].query_id(int(info.id)) is info


@pytest.mark.parametrize("name", list(ONTOLOGY_CASES))
@settings(max_examples=50)
@given(data=st.data())
def test_name_lookup_ignores_case(name, data):
    lookup = ONTOLOGY_CASES[name][0]
    info = data.draw(st.sampled_from(lookup.values()))
    found = lookup.query_name(_random_case(data.draw, info.name))
    assert found is not None and found.name.lower() == info.name.lower()


@pytest.mark.parametrize("name", list(ONTOLOGY_CASES))
@pytest.mark.parametrize("key", [None, 1.5, b"21", ("21",)])
def test_unsupported_key_types_are_not_found(name, key):
    # Regression: these raised AttributeError/TypeError from ``key.lower()``.
    lookup = ONTOLOGY_CASES[name][0]
    assert key not in lookup
    assert lookup.get(key) is None
    with pytest.raises(KeyError):
        lookup[key]
