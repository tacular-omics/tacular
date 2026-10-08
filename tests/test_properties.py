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


def test_every_isotope_string_key_matches_its_tuple_key():
    """Catches a broken "13C"-style key parser or an isotope missing from the string index:
    every isotope in the table must resolve to the same entry by "<A><symbol>" and by
    (symbol, A)."""
    wrong = []
    for symbol, mass_number in ISOTOPES:
        key = f"{mass_number}{symbol}"
        if key not in ELEMENT_LOOKUP or ELEMENT_LOOKUP[key] is not ELEMENT_LOOKUP[(symbol, mass_number)]:
            wrong.append(key)
    assert not wrong, f"{len(wrong)} isotope keys do not resolve to their tuple key: {wrong[:10]}"


def test_every_isotope_string_key_rejects_leading_zeros():
    """Catches a parser that strips leading zeros, which would read "013C" as 13C and
    silently accept malformed isotope labels."""
    accepted = []
    for symbol, mass_number in ISOTOPES:
        for zeros in ("0", "00"):
            key = f"{zeros}{mass_number}{symbol}"
            if key in ELEMENT_LOOKUP:
                accepted.append(key)
                continue
            with pytest.raises(TacularKeyError, match="leading zero"):
                ELEMENT_LOOKUP[key]
    assert not accepted, f"{len(accepted)} zero-padded isotope keys accepted: {accepted[:10]}"


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


def _id_variants(info, accession, id_prefix):
    bare = info.id.removeprefix(id_prefix)
    for body in {bare, bare.lstrip("0") or "0", "00" + bare}:
        for key in (id_prefix + body, accession + id_prefix + body):
            yield from {key, key.lower(), key.upper(), key.swapcase()}


@pytest.mark.parametrize("name", list(ONTOLOGY_CASES))
def test_every_id_key_variant_resolves_to_its_entry(name):
    """Catches id normalization bugs (accession prefix, case, zero padding, int keys) that
    send a valid id to the wrong entry or to nothing, for every entry of the ontology."""
    lookup, accession, id_prefix = ONTOLOGY_CASES[name]
    wrong = []
    for info in lookup.values():
        for key in _id_variants(info, accession, id_prefix):
            if lookup.query_id(key) is not info:
                wrong.append((info.id, key))
        if info.id.isdigit() and lookup.query_id(int(info.id)) is not info:
            wrong.append((info.id, int(info.id)))
    assert not wrong, f"{len(wrong)} {name} id keys resolve to the wrong entry: {wrong[:10]}"


@pytest.mark.parametrize("name", list(ONTOLOGY_CASES))
def test_every_name_resolves_to_its_entry_in_any_case(name):
    """Catches a broken case-insensitive name index and two entries whose names differ only
    in case, where the later one would shadow the earlier in ``query_name``."""
    lookup = ONTOLOGY_CASES[name][0]
    wrong = []
    for info in lookup.values():
        for key in {info.name, info.name.lower(), info.name.upper(), info.name.swapcase()}:
            if lookup.query_name(key) is not info:
                wrong.append((info.id, key))
    assert not wrong, f"{len(wrong)} {name} names resolve to the wrong entry: {wrong[:10]}"


@pytest.mark.parametrize("name", list(ONTOLOGY_CASES))
@pytest.mark.parametrize("key", [None, 1.5, b"21", ("21",)])
def test_unsupported_key_types_are_not_found(name, key):
    # Regression: these raised AttributeError/TypeError from ``key.lower()``.
    lookup = ONTOLOGY_CASES[name][0]
    assert key not in lookup
    assert lookup.get(key) is None
    with pytest.raises(KeyError):
        lookup[key]
