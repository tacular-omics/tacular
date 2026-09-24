"""tacular 2.0 API: error hierarchy, constants, prefixed ids, the unified lookup
surface, keyword-only options, frozen value types and deterministic ``to_dict``."""

import dataclasses
import inspect
import json

import pytest

import tacular as t
from tacular import TacularError, TacularKeyError, constants
from tacular.obo_lookup import OntologyLookup, _normalize_id
from tacular.unimod.dclass import UnimodInfo

ALL_LOOKUPS = [
    t.AA_LOOKUP,
    t.ELEMENT_LOOKUP,
    t.FRAGMENT_ION_LOOKUP,
    t.NEUTRAL_DELTA_LOOKUP,
    t.PROTEASE_LOOKUP,
    t.REFMOL_LOOKUP,
    t.MONOSACCHARIDE_LOOKUP,
    t.UNIMOD_LOOKUP,
    t.PSIMOD_LOOKUP,
    t.RESID_LOOKUP,
    t.XLMOD_LOOKUP,
    t.GNO_LOOKUP,
    t.UNIPROT_PTM_LOOKUP,
]
IDS = [type(lk).__name__ for lk in ALL_LOOKUPS]


# --- errors ---------------------------------------------------------------------------


def test_error_hierarchy():
    assert issubclass(TacularError, ValueError)
    assert issubclass(TacularKeyError, TacularError)
    assert issubclass(TacularKeyError, KeyError)
    assert str(TacularKeyError("plain message")) == "plain message"
    assert str(TacularKeyError("a", "b")) == "('a', 'b')"


@pytest.mark.parametrize("lookup", ALL_LOOKUPS, ids=IDS)
def test_every_lookup_miss_raises_tacular_key_error(lookup):
    for bad in ("definitely-not-a-key-xyz", None, 3.5, object()):
        with pytest.raises(TacularKeyError):
            lookup[bad]
        assert bad not in lookup
        assert lookup.get(bad) is None


# --- constants ------------------------------------------------------------------------


def test_constants_match_element_data():
    assert constants.PROTON_MASS == pytest.approx(1.007276466621)
    assert constants.HYDROGEN_MASS == t.ELEMENT_LOOKUP.get_mass("1H")
    assert constants.PROTON_MASS + constants.ELECTRON_MASS == pytest.approx(
        constants.HYDROGEN_MASS, abs=1e-7
    )  # 13.6 eV binding
    c13 = t.ELEMENT_LOOKUP.get_mass("13C") - t.ELEMENT_LOOKUP.get_mass("12C")
    assert constants.C13_C12_MASS_DIFF == pytest.approx(c13, abs=1e-9)
    assert constants.NEUTRON_MASS == pytest.approx(1.00866491595)
    assert set(constants.__all__) == {
        "PROTON_MASS",
        "ELECTRON_MASS",
        "NEUTRON_MASS",
        "HYDROGEN_MASS",
        "C13_C12_MASS_DIFF",
    }


# --- prefixed ids -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("lookup", "keys", "expected_id"),
    [
        (t.UNIMOD_LOOKUP, ["UNIMOD:21", "U:21", "u:0021", " unimod:21 ", 21, "U:Phospho", "Phospho"], "21"),
        (t.PSIMOD_LOOKUP, ["MOD:00046", "M:00046", "46", 46, "M:O-phospho-L-serine"], "00046"),
        (t.RESID_LOOKUP, ["RESID:AA0002", "R:AA0002", "AA0002", "aa2", "2", 2], "AA0002"),
        (t.XLMOD_LOOKUP, ["XLMOD:01000", "X:01000", "01000", 1000], "01000"),
        (t.GNO_LOOKUP, ["GNO:G00008BG", "G:G00008BG", "G00008BG", "g8bg"], "G00008BG"),
        (t.UNIPROT_PTM_LOOKUP, ["PTM-0476", "ptm-476", "0476", 476], "0476"),
    ],
)
def test_prefixed_ids_resolve(lookup, keys, expected_id):
    for key in keys:
        assert lookup[key].id == expected_id, key


def test_foreign_prefix_does_not_resolve():
    assert "MOD:00046" not in t.UNIMOD_LOOKUP
    assert "U:21" not in t.PSIMOD_LOOKUP


def test_normalize_id_is_the_single_path():
    assert _normalize_id("U:0021", ("unimod:", "u:")) == "21"
    assert _normalize_id("0000", ()) == ""
    assert t.UNIMOD_LOOKUP.query_id(True) is None  # type: ignore[arg-type]
    assert t.UNIMOD_LOOKUP.query_id(None) is None  # type: ignore[arg-type]
    assert t.UNIMOD_LOOKUP.query_name(None) is None  # type: ignore[arg-type]


def _entity(id_: str, name: str, mass: float | None = None, comp: dict | None = None) -> UnimodInfo:
    return UnimodInfo(id_, name, None, mass, mass, comp)


def test_ontology_lookup_rejects_duplicates():
    dup_id = OntologyLookup({"1": _entity("1", "A"), "01": _entity("01", "B")}, "T")
    with pytest.raises(TacularError, match="Duplicate id"):
        dup_id["A"]
    dup_name = OntologyLookup({"1": _entity("1", "A"), "2": _entity("2", "a")}, "T")
    with pytest.raises(TacularError, match="Duplicate name"):
        dup_name["1"]


def test_choice_is_keyword_only_and_raises_tacular_error():
    lookup = OntologyLookup({"1": _entity("1", "A")}, "T")
    with pytest.raises(TacularError, match="No T entries"):
        lookup.choice()
    assert lookup.choice(require_monoisotopic_mass=False, require_composition=False).id == "1"
    with pytest.raises(TacularError):
        lookup.choice(require_monoisotopic_mass=False)
    with pytest.raises(TacularError):
        lookup.choice(require_composition=False)
    with pytest.raises(TypeError):
        lookup.choice(False, False)  # type: ignore[misc]


def test_ontology_lookup_version_and_repr():
    lookup = OntologyLookup({"1": _entity("1", "A")}, "T", version="v9")
    assert lookup.version == "v9"
    assert repr(lookup) == "<OntologyLookup T vv9: 1 entries>"


# --- unified lookup surface -------------------------------------------------------------


@pytest.mark.parametrize("lookup", ALL_LOOKUPS, ids=IDS)
def test_items_keys_values_agree(lookup):
    items = lookup.items()
    assert [k for k, _ in items] == lookup.keys()
    assert [v for _, v in items] == lookup.values() == list(lookup)
    assert len(items) == len(lookup)
    assert repr(lookup).startswith(f"<{type(lookup).__name__}")


def test_aa_query_methods_return_none():
    assert t.AA_LOOKUP.query_one_letter("A") is t.AA_LOOKUP["A"]
    assert t.AA_LOOKUP.query_three_letter("ala") is t.AA_LOOKUP["A"]
    assert t.AA_LOOKUP.query_name("ALANINE") is t.AA_LOOKUP["A"]
    for method in (t.AA_LOOKUP.query_one_letter, t.AA_LOOKUP.query_three_letter, t.AA_LOOKUP.query_name):
        assert method("nope") is None
        assert method(None) is None  # type: ignore[arg-type]
    assert t.ORDERED_AMINO_ACIDS == t.AA_LOOKUP.keys()


def test_aa_missing_mass_and_composition_raise_tacular_error():
    with pytest.raises(TacularError, match="monoisotopic mass"):
        t.AA_LOOKUP.get_mass("B")
    with pytest.raises(TacularError, match="average mass"):
        t.AA_LOOKUP.get_mass("B", monoisotopic=False)
    with pytest.raises(TacularError, match="composition"):
        t.AA_LOOKUP.composition("B")


def test_other_lookup_queries():
    assert t.FRAGMENT_ION_LOOKUP.query_ion_type(t.IonType.Y) is t.FRAGMENT_ION_LOOKUP["y"]
    assert t.FRAGMENT_ION_LOOKUP.query_id(None) is None  # type: ignore[arg-type]
    assert t.NEUTRAL_DELTA_LOOKUP.query_delta(t.NeutralDelta.WATER) is t.NEUTRAL_DELTA_LOOKUP["water"]
    assert t.PROTEASE_LOOKUP.query_id("TRYPSIN") is t.PROTEASE_LOOKUP[t.Protease.TRYPSIN]
    assert t.REFMOL_LOOKUP.query_id(t.RefMolID("TMT126")) is t.REFMOL_LOOKUP["tmt126"]
    assert t.REFMOL_LOOKUP.query_id(None) is None  # type: ignore[arg-type]
    assert t.MONOSACCHARIDE_LOOKUP.query_name("HEX") is t.MONOSACCHARIDE_LOOKUP["Hex"]


# --- keyword-only options, frozen values, to_dict --------------------------------------

INFOS = [
    t.AA_LOOKUP["A"],
    t.ELEMENT_LOOKUP["13C"],
    t.FRAGMENT_ION_LOOKUP["y"],
    t.NEUTRAL_DELTA_LOOKUP["H2O"],
    t.REFMOL_LOOKUP["TMT126"],
    t.MONOSACCHARIDE_LOOKUP["Hex"],
    t.UNIMOD_LOOKUP["Phospho"],
]


@pytest.mark.parametrize("info", INFOS, ids=lambda i: type(i).__name__)
def test_info_options_are_keyword_only(info):
    for method in (info.get_mass, info.to_dict):
        for param in inspect.signature(method).parameters.values():
            assert param.kind is inspect.Parameter.KEYWORD_ONLY, (method, param)


@pytest.mark.parametrize("info", [*INFOS, t.PROTEASE_LOOKUP["trypsin"]], ids=lambda i: type(i).__name__)
def test_info_is_frozen_slotted_value(info):
    assert dataclasses.is_dataclass(info)
    assert not hasattr(info, "__dict__")
    field = dataclasses.fields(info)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(info, field, "x")
    hash(info)


@pytest.mark.parametrize("info", INFOS, ids=lambda i: type(i).__name__)
def test_to_dict_is_json_and_precision_is_optional(info):
    rounded = info.to_dict()
    full = info.to_dict(float_precision=None)
    json.dumps(rounded)
    assert set(rounded) == set(full)
    assert "dict_composition" not in rounded
    mass_key = "mass" if "mass" in full else "monoisotopic_mass"
    assert full[mass_key] == pytest.approx(rounded[mass_key], abs=1e-6)


def test_to_dict_keys():
    assert t.ELEMENT_LOOKUP["13C"].to_dict()["is_monoisotopic"] is False
    aa = t.AA_LOOKUP["J"].to_dict()
    assert aa["is_ambiguous"] is True
    assert aa["is_mass_ambiguous"] is False
    assert "formula" in t.REFMOL_LOOKUP["TMT126"].to_dict()
    assert not hasattr(t.REFMOL_LOOKUP["TMT126"], "chemical_formula")


def test_neutral_delta_to_dict_is_deterministic():
    info = t.NEUTRAL_DELTA_LOOKUP["H2O"]
    assert len(info.amino_acids) > 1
    assert info.to_dict()["amino_acids"] == sorted(info.amino_acids)
    shuffled = dataclasses.replace(info, amino_acids=frozenset(reversed(sorted(info.amino_acids))))
    assert shuffled.to_dict() == info.to_dict()


def test_element_info_errors_and_update():
    carbon = t.ELEMENT_LOOKUP["C"]
    with pytest.raises(TacularError, match="no neutron count"):
        _ = carbon.neutron_count
    with pytest.raises(TacularError, match="zero"):
        carbon.serialize(0)
    heavier = carbon.update(mass=99.0)
    assert heavier.mass == 99.0
    assert carbon.mass != 99.0
    with pytest.raises(TypeError):
        carbon.update(not_a_field=1)


def test_element_abundance_pairs_report_zero_for_missing_abundance():
    pairs = t.ELEMENT_LOOKUP.get_masses_and_abundances("Tc")
    assert pairs
    assert all(isinstance(abundance, float) for _, abundance in pairs)


def test_fragment_ion_missing_values_raise_tacular_error():
    info = dataclasses.replace(
        t.FRAGMENT_ION_LOOKUP["y"], monoisotopic_mass=None, average_mass=None, dict_composition=None
    )
    with pytest.raises(TacularError, match="Monoisotopic mass"):
        info.get_mass()
    with pytest.raises(TacularError, match="Average mass"):
        info.get_mass(monoisotopic=False)
    with pytest.raises(TacularError, match="Composition"):
        _ = info.composition
    assert t.FRAGMENT_ION_LOOKUP["z."].ion_type is t.IonType.Z_RADICAL
    plain = dataclasses.replace(t.FRAGMENT_ION_LOOKUP["y"], id="y")
    assert plain.ion_type is t.IonType.Y


def test_protease_pattern_is_compiled_regex():
    trypsin = t.PROTEASE_LOOKUP["trypsin"]
    assert trypsin.pattern.pattern == trypsin.regex
    assert "pattern" not in dataclasses.asdict(trypsin)
    assert trypsin.to_dict()["id"] == "trypsin"


# --- exports ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    [
        "Proteases",
        "PROTEASE_LITERALS",
        "PROTEASES_DICT",
        "XlModInfo",
        "XlModLookup",
    ],
)
def test_renamed_names_are_gone(name):
    assert not hasattr(t, name)


def test_new_exports():
    for name in ("TacularError", "TacularKeyError", "ElementKey", "Protease", "ProteaseLiteral", "PROTEASE_DICT"):
        assert name in t.__all__
    assert t.constants is constants
    assert not hasattr(t.OboEntity, "mass")
    assert not hasattr(t.ElementLookup, "mass")
    assert not hasattr(t.AALookup, "one_letter")
    assert not hasattr(t.MonosaccharideLookup, "proforma")
