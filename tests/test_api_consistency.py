"""Cross-lookup API consistency (1.2.0): hashing, non-string keys, the shared
get/keys/values/len surface, exports, and callers not aliasing cached state."""

import dataclasses
import importlib
import inspect
import pkgutil
import re
from collections import Counter
from pathlib import Path

import pytest

import tacular
from tacular import (
    AA_LOOKUP,
    ELEMENT_LOOKUP,
    FRAGMENT_ION_LOOKUP,
    GNO_LOOKUP,
    ISOBARIC_TAG_LOOKUP,
    MONOSACCHARIDE_LOOKUP,
    NEUTRAL_DELTA_LOOKUP,
    PROTEASE_LOOKUP,
    PSIMOD_LOOKUP,
    REFMOL_LOOKUP,
    RESID_LOOKUP,
    SILAC_LOOKUP,
    UNIMOD_LOOKUP,
    UNIPROT_PTM_LOOKUP,
    XLMOD_LOOKUP,
    MonosaccharideInfo,
    OboEntity,
    TacularKeyError,
)

ONTOLOGY_LOOKUPS = [UNIMOD_LOOKUP, PSIMOD_LOOKUP, RESID_LOOKUP, XLMOD_LOOKUP, GNO_LOOKUP, UNIPROT_PTM_LOOKUP]
OTHER_LOOKUPS = [
    AA_LOOKUP,
    PROTEASE_LOOKUP,
    FRAGMENT_ION_LOOKUP,
    MONOSACCHARIDE_LOOKUP,
    NEUTRAL_DELTA_LOOKUP,
    REFMOL_LOOKUP,
    ISOBARIC_TAG_LOOKUP,
    SILAC_LOOKUP,
]
ALL_LOOKUPS = ONTOLOGY_LOOKUPS + OTHER_LOOKUPS + [ELEMENT_LOOKUP]


def _ids(lookups):
    return [type(lk).__name__ for lk in lookups]


# --- 1. hashing -------------------------------------------------------------


def _one_of_each_info():
    return [
        UNIMOD_LOOKUP["Phospho"],
        PSIMOD_LOOKUP["MOD:00046"],
        RESID_LOOKUP["AA0002"],
        next(iter(XLMOD_LOOKUP)),
        next(iter(GNO_LOOKUP)),
        next(iter(UNIPROT_PTM_LOOKUP)),
        MONOSACCHARIDE_LOOKUP["Hex"],
        AA_LOOKUP["A"],
        FRAGMENT_ION_LOOKUP["b"],
        next(iter(REFMOL_LOOKUP)),
        NEUTRAL_DELTA_LOOKUP["H2O"],
        PROTEASE_LOOKUP["trypsin"],
        ELEMENT_LOOKUP["C"],
        ISOBARIC_TAG_LOOKUP["TMT10"],
        ISOBARIC_TAG_LOOKUP["TMT10"].reporter_ions[0],
        SILAC_LOOKUP["Lys8"],
    ]


@pytest.mark.parametrize("info", _one_of_each_info(), ids=lambda i: type(i).__name__)
def test_every_info_class_is_hashable(info):
    h = hash(info)
    assert isinstance(h, int)
    assert {info: 1}[info] == 1
    # equal copies hash equal
    if dataclasses.is_dataclass(info):
        assert hash(dataclasses.replace(info)) == h


@pytest.mark.parametrize("lookup", ONTOLOGY_LOOKUPS, ids=_ids(ONTOLOGY_LOOKUPS))
def test_every_ontology_entry_hashes(lookup):
    assert len({info for info in lookup}) == len(lookup)


def test_obo_entity_hash_is_id_and_name():
    info = UNIMOD_LOOKUP["Phospho"]
    assert hash(info) == hash((info.id, info.name))
    # a mass update keeps the hash, as documented on OboEntity.__hash__
    assert hash(info.update(monoisotopic_mass=1.0)) == hash(info)


def test_monosaccharide_info_is_frozen_slotted_dataclass():
    info = MONOSACCHARIDE_LOOKUP["Hex"]
    assert dataclasses.is_dataclass(MonosaccharideInfo)
    assert "__slots__" in MonosaccharideInfo.__dict__
    assert not hasattr(info, "__dict__")
    with pytest.raises(dataclasses.FrozenInstanceError):
        info.name = "x"  # type: ignore[misc]
    assert isinstance(info, OboEntity)


# --- 3. non-string keys -------------------------------------------------------

BAD_KEYS = [None, 1.5, object(), [], {}]


@pytest.mark.parametrize("lookup", ALL_LOOKUPS, ids=_ids(ALL_LOOKUPS))
@pytest.mark.parametrize("key", BAD_KEYS, ids=lambda k: type(k).__name__)
def test_bad_key_types_are_not_found(lookup, key):
    sentinel = object()
    assert (key in lookup) is False
    assert lookup.get(key) is None
    assert lookup.get(key, sentinel) is sentinel
    with pytest.raises(KeyError):
        lookup[key]


@pytest.mark.parametrize("lookup", OTHER_LOOKUPS, ids=_ids(OTHER_LOOKUPS))
def test_int_keys_not_found_on_string_lookups(lookup):
    assert (42 in lookup) is False
    assert lookup.get(42) is None
    with pytest.raises(KeyError):
        lookup[42]


def test_element_get_returns_default_for_bad_input():
    assert ELEMENT_LOOKUP.get("c") is None
    assert ELEMENT_LOOKUP.get("") is None
    assert ELEMENT_LOOKUP.get("13") is None
    assert ELEMENT_LOOKUP.get(("C", "x")) is None  # type: ignore[arg-type]
    assert ELEMENT_LOOKUP.get("c", "d") == "d"  # type: ignore[arg-type]


def test_element_getitem_errors_are_tacular_key_errors():
    # bad input and wrong key types both raise TacularKeyError: a KeyError and a ValueError
    for bad in ("c", None, ("C", 12, 1), 3.5):
        with pytest.raises(TacularKeyError) as exc_info:
            ELEMENT_LOOKUP[bad]  # type: ignore[index]
        assert isinstance(exc_info.value, KeyError)
        assert isinstance(exc_info.value, ValueError)
        assert not isinstance(exc_info.value, TypeError)


# --- 4. unified lookup surface --------------------------------------------------


@pytest.mark.parametrize("lookup", ALL_LOOKUPS, ids=_ids(ALL_LOOKUPS))
def test_common_lookup_surface(lookup):
    n = len(lookup)
    assert n > 0
    values = lookup.values()
    keys = lookup.keys()
    assert isinstance(values, list)
    assert isinstance(keys, list)
    assert len(values) == n
    assert len(keys) == n
    assert list(lookup) == values
    for key, value in zip(keys, values, strict=True):
        assert lookup[key] is value or lookup[key] == value
        assert key in lookup
        assert lookup.get(key) is not None
    # the returned lists are copies
    values.clear()
    keys.clear()
    assert len(lookup.values()) == n
    assert len(lookup.keys()) == n


@pytest.mark.parametrize("lookup", ALL_LOOKUPS, ids=_ids(ALL_LOOKUPS))
def test_get_has_default_param(lookup):
    params = inspect.signature(lookup.get).parameters
    assert "default" in params
    sentinel = object()
    assert lookup.get("definitely-not-a-key-xyz", sentinel) is sentinel


def test_neutral_delta_get():
    assert NEUTRAL_DELTA_LOOKUP.get("H2O") is NEUTRAL_DELTA_LOOKUP["H2O"]
    assert NEUTRAL_DELTA_LOOKUP.get("nope") is None


def test_monosaccharide_protease_refmol_get_default():
    assert MONOSACCHARIDE_LOOKUP.get("nope", 1) == 1  # type: ignore[arg-type]
    assert PROTEASE_LOOKUP.get("nope", 1) == 1  # type: ignore[arg-type]
    assert REFMOL_LOOKUP.get("nope", 1) == 1  # type: ignore[arg-type]


# --- 5. exports -------------------------------------------------------------------


@pytest.mark.parametrize("name", ["ProteaseLookup", "OntologyLookup", "ModLocation"])
def test_new_top_level_exports(name):
    assert name in tacular.__all__
    assert getattr(tacular, name) is not None


def test_all_names_resolve():
    for name in tacular.__all__:
        assert hasattr(tacular, name), name
    assert len(tacular.__all__) == len(set(tacular.__all__))


# --- 6 / 9. no aliasing of internal state -----------------------------------------


def test_refmol_query_lists_are_copies():
    label = next(iter(REFMOL_LOOKUP)).label_type
    mol_type = next(iter(REFMOL_LOOKUP)).molecule_type
    got = REFMOL_LOOKUP.query_label_type(label)
    n = len(got)
    got.clear()
    assert len(REFMOL_LOOKUP.query_label_type(label)) == n
    got = REFMOL_LOOKUP.query_molecule_type(mol_type)
    n = len(got)
    got.clear()
    assert len(REFMOL_LOOKUP.query_molecule_type(mol_type)) == n


def _composition_sources():
    return [
        ("FragmentIonInfo", lambda: FRAGMENT_ION_LOOKUP["y"].composition),
        ("AminoAcidInfo", lambda: AA_LOOKUP["G"].composition),
        ("AALookup.composition", lambda: AA_LOOKUP.composition("G")),
        ("RefMolInfo", lambda: next(iter(REFMOL_LOOKUP)).composition),
        ("NeutralDeltaInfo", lambda: NEUTRAL_DELTA_LOOKUP["H2O"].composition),
        ("UnimodInfo", lambda: UNIMOD_LOOKUP["Phospho"].composition),
    ]


@pytest.mark.parametrize("get_comp", [g for _, g in _composition_sources()], ids=[n for n, _ in _composition_sources()])
def test_returned_composition_is_a_copy(get_comp):
    comp = get_comp()
    before = dict(comp)
    comp[ELEMENT_LOOKUP["C"]] = comp.get(ELEMENT_LOOKUP["C"], 0) + 1000
    comp.clear()
    assert dict(get_comp()) == before


def test_composition_is_still_a_counter():
    assert isinstance(FRAGMENT_ION_LOOKUP["y"].composition, Counter)
    assert isinstance(AA_LOOKUP["G"].composition, Counter)
    assert isinstance(next(iter(REFMOL_LOOKUP)).composition, Counter)
    assert isinstance(NEUTRAL_DELTA_LOOKUP["H2O"].composition, Counter)


# --- 7. docs -----------------------------------------------------------------------


def _lookup_classes():
    classes = []
    for mod in pkgutil.iter_modules(tacular.__path__):
        if not mod.ispkg or mod.name.startswith("_"):
            continue
        try:
            lookup_mod = importlib.import_module(f"tacular.{mod.name}.lookup")
        except ModuleNotFoundError:
            continue
        for _, obj in inspect.getmembers(lookup_mod, inspect.isclass):
            if obj.__module__ == lookup_mod.__name__ and obj.__name__.endswith("Lookup"):
                classes.append(obj)
    return classes


@pytest.mark.parametrize("cls", _lookup_classes(), ids=lambda c: c.__name__)
def test_lookup_classes_have_docstrings(cls):
    assert cls.__dict__.get("__doc__"), f"{cls.__name__} has no class docstring"


def test_element_lookup_docs_do_not_promise_generated_isotopes():
    from tacular.elements.lookup import ElementLookup

    docs = " ".join(
        d or ""
        for d in (
            ElementLookup.__doc__,
            ElementLookup.__getitem__.__doc__,
            ElementLookup.get_isotope.__doc__,
            ElementLookup.get_all_isotopes.__doc__,
        )
    )
    assert not re.search(r"auto_generate|include_generated|automatically generated", docs)
    assert ElementLookup.keys.__annotations__["return"] != list[tuple[str, int | None]]


# --- 8. generated data modules fail loudly ------------------------------------------

DATA_MODULES = ["elements", "unimod", "psimod", "resid", "xlmod", "gno", "uniprot_ptm", "monosaccharides"]
SRC = Path(tacular.__file__).parent
GEN = Path(__file__).resolve().parents[1] / "data_gen" / "generator"


@pytest.mark.parametrize("name", DATA_MODULES)
def test_generated_data_does_not_swallow_errors(name):
    text = (SRC / name / "data.py").read_text(encoding="utf-8")
    assert "UserWarning" not in text
    assert "Using empty dictionaries" not in text


@pytest.mark.skipif(not GEN.is_dir(), reason="data_gen not available (installed wheel)")
def test_generator_templates_do_not_swallow_errors():
    for path in GEN.glob("gen_*.py"):
        text = path.read_text(encoding="utf-8")
        assert "Using empty dictionaries" not in text, path.name


@pytest.mark.parametrize("lookup", OTHER_LOOKUPS, ids=_ids(OTHER_LOOKUPS))
def test_non_ontology_keys_are_plain_strings(lookup):
    assert all(type(k) is str for k in lookup.keys())
