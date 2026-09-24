"""Tests for the cached / indexed fast paths: they must behave exactly like the plain code
they replace (memoized ``ElementInfo`` hash, per-instance resolved composition, the
mass-sorted ``query_mass`` index, the ``query_id`` exact-key fast path, lazy ontology
imports)."""

import dataclasses
import math
import pickle
import subprocess
import sys

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import tacular as t
from tacular.obo_entity import OboEntity
from tacular.obo_lookup import OntologyLookup, _normalize_id

ONTOLOGY_LOOKUPS = [
    t.UNIMOD_LOOKUP,
    t.PSIMOD_LOOKUP,
    t.RESID_LOOKUP,
    t.XLMOD_LOOKUP,
    t.GNO_LOOKUP,
    t.UNIPROT_PTM_LOOKUP,
]

# --- ElementInfo hash -------------------------------------------------------------------


def test_element_info_hash_is_memoized_and_matches_str_hash():
    c13 = t.ELEMENT_LOOKUP["13C"]
    fresh = pickle.loads(pickle.dumps(c13))
    with pytest.raises(AttributeError):
        _ = fresh._hash  # not pickled: str hashes are salted per process
    assert hash(fresh) == hash("13C") == hash(c13)
    assert fresh._hash == hash("13C")
    assert {c13: 1}["13C"] == 1
    assert {"13C": 1}[c13] == 1


def test_element_info_hash_slot_is_not_a_field():
    c = t.ELEMENT_LOOKUP["C"]
    hash(c)
    assert "_hash" not in {f.name for f in dataclasses.fields(c)}
    assert "_hash" not in dataclasses.asdict(c)
    assert "_hash" not in repr(c)
    assert not hasattr(c, "__dict__")
    with pytest.raises((dataclasses.FrozenInstanceError, TypeError)):  # TypeError: CPython slots+frozen quirk
        c._hash = 1  # type: ignore[misc]


def test_element_info_replace_rehashes():
    c = t.ELEMENT_LOOKUP["C"]
    hash(c)
    heavier = dataclasses.replace(c, mass_number=13)
    assert hash(heavier) == hash("13C")


# --- resolved composition ---------------------------------------------------------------

COMPOSITION_INFOS = [
    t.AA_LOOKUP["W"],
    t.FRAGMENT_ION_LOOKUP["y"],
    t.NEUTRAL_DELTA_LOOKUP["H2O"],
    t.REFMOL_LOOKUP["TMT126"],
]


@pytest.mark.parametrize("info", COMPOSITION_INFOS, ids=lambda i: type(i).__name__)
def test_composition_is_resolved_once_and_copied(info):
    first = info.composition
    resolved = info._resolved_composition
    second = info.composition
    assert info._resolved_composition is resolved
    assert first == second == resolved
    assert first is not resolved and second is not first
    assert type(first) is type(resolved)
    first[t.ELEMENT_LOOKUP["C"]] += 100
    del second[next(iter(second))]
    assert info.composition == resolved
    assert {str(k): v for k, v in info.composition.items()} == dict(info.dict_composition)


@pytest.mark.parametrize("info", COMPOSITION_INFOS, ids=lambda i: type(i).__name__)
def test_composition_cache_survives_pickle_and_is_not_a_field(info):
    _ = info.composition
    restored = pickle.loads(pickle.dumps(info))
    with pytest.raises(AttributeError):
        _ = restored._resolved_composition
    assert restored.composition == info.composition
    assert "_resolved_composition" not in dataclasses.asdict(info)
    assert "_resolved_composition" not in repr(info)


def test_amino_acid_without_composition_is_none():
    b = t.AA_LOOKUP["B"]
    assert b.dict_composition is None
    assert b.composition is None
    assert t.AA_LOOKUP["X"].composition == {}


# --- query_mass: the sorted index must equal the old linear scan ------------------------


def _query_mass_linear(lookup, mass, tolerance=0.01, monoisotopic=True):
    """A linear scan over the same ``tolerance_window`` bounds, kept as the reference."""
    matches = []
    if not math.isfinite(mass):  # documented: a NaN or infinite mass matches nothing
        return matches
    for info in lookup._data.values():
        mod_mass = info.monoisotopic_mass if monoisotopic else info.average_mass
        if mod_mass is not None and mass - tolerance <= mod_mass <= mass + tolerance:
            matches.append(info)
    return matches


def _entity(i, mass, avg=None):
    return OboEntity(
        id=str(i), name=f"e{i}", formula=None, monoisotopic_mass=mass, average_mass=avg, dict_composition=None
    )


# Ties, None, NaN, infinities and out-of-order masses, to pin down ordering and edge cases.
_SYNTHETIC = OntologyLookup(
    {
        str(i): _entity(i, m, a)
        for i, (m, a) in enumerate(
            [
                (10.0, 10.1),
                (5.0, None),
                (10.0, 10.1),
                (None, 3.0),
                (math.nan, math.nan),
                (-2.5, -2.4),
                (math.inf, 7.0),
                (10.004, -math.inf),
                (0.0, 0.0),
                (9.996, 10.0),
            ]
        )
    },
    "SYN",
)

_FLOATS = st.floats(allow_nan=True, allow_infinity=True, width=64)


@settings(max_examples=300, deadline=None)
@given(
    lookup=st.sampled_from([*ONTOLOGY_LOOKUPS, _SYNTHETIC]),
    mass=st.one_of(_FLOATS, st.floats(min_value=-50, max_value=3000), st.sampled_from([10.0, 79.966331, 15.994915])),
    tolerance=st.one_of(_FLOATS, st.floats(min_value=0, max_value=5), st.just(0.0)),
    monoisotopic=st.booleans(),
)
def test_query_mass_matches_linear_scan(lookup, mass, tolerance, monoisotopic):
    got = lookup.query_mass(mass, tolerance=tolerance, monoisotopic=monoisotopic)
    assert got == _query_mass_linear(lookup, mass, tolerance, monoisotopic)


@pytest.mark.parametrize("lookup", ONTOLOGY_LOOKUPS, ids=lambda lk: lk.ontology_name)
@pytest.mark.parametrize("monoisotopic", [True, False])
def test_query_mass_matches_linear_scan_at_every_entry_mass(lookup, monoisotopic):
    for info in list(lookup)[::7]:
        mass = info.get_mass(monoisotopic=monoisotopic)
        if mass is None:
            continue
        for tolerance in (0.0, 1e-9, 0.01, 1.0):
            got = lookup.query_mass(mass, tolerance=tolerance, monoisotopic=monoisotopic)
            assert got == _query_mass_linear(lookup, mass, tolerance, monoisotopic)


def test_query_mass_synthetic_edges():
    by_name = {info.name: info for info in _SYNTHETIC}
    assert [i.name for i in _SYNTHETIC.query_mass(10.0, tolerance=0.005)] == ["e0", "e2", "e7", "e9"]
    assert _SYNTHETIC.query_mass(math.nan, tolerance=math.inf) == []
    assert _SYNTHETIC.query_mass(10.0, tolerance=-1.0) == []
    everything = _SYNTHETIC.query_mass(0.0, tolerance=math.inf)
    assert by_name["e6"] in everything and by_name["e4"] not in everything
    assert [i.name for i in _SYNTHETIC.query_mass(10.0, tolerance=0.0, monoisotopic=False)] == ["e9"]


# --- query_id exact-key fast path -------------------------------------------------------


@pytest.mark.parametrize("lookup", ONTOLOGY_LOOKUPS, ids=lambda lk: lk.ontology_name)
def test_exact_id_keys_normalize_to_the_same_entry(lookup):
    index = lookup._index
    assert set(lookup.keys()) <= set(index.by_exact_id)
    for key, info in index.by_exact_id.items():
        assert index.by_id.get(_normalize_id(key, lookup._accession_prefixes, lookup._id_prefix)) is info


def _query_id_slow(lookup, key):
    return lookup._index.by_id.get(_normalize_id(key, lookup._accession_prefixes, lookup._id_prefix))


@pytest.mark.parametrize("lookup", ONTOLOGY_LOOKUPS, ids=lambda lk: lk.ontology_name)
def test_query_id_fast_path_matches_normalization_on_every_key(lookup):
    for raw_id in lookup.keys():
        for variant in (raw_id, raw_id.lower(), raw_id.upper(), f" {raw_id} ", "0" + raw_id):
            assert lookup.query_id(variant) is _query_id_slow(lookup, variant)


_ID_CHARS = st.text(alphabet="0123456789aAgGuUmMrRxX:BbN _", max_size=10)


@settings(max_examples=300, deadline=None)
@given(lookup=st.sampled_from(ONTOLOGY_LOOKUPS), key=st.one_of(_ID_CHARS, st.text(max_size=8)))
def test_query_id_matches_normalization(lookup, key):
    assert lookup.query_id(key) is _query_id_slow(lookup, key)


def test_prefixed_raw_ids_are_not_fast_pathed():
    # A raw id that itself starts with an accession prefix must still be normalized.
    e = _entity(1, None)
    odd = OboEntity(
        id="x:5", name="odd", formula=None, monoisotopic_mass=None, average_mass=None, dict_composition=None
    )
    lookup = OntologyLookup({"1": e, "x:5": odd}, "T", accession_prefixes=("x:",), id_prefix="g")
    assert "x:5" not in lookup._index.by_exact_id
    assert lookup.query_id("x:5") is _query_id_slow(lookup, "x:5")
    g = OboEntity(id="GG7", name="g", formula=None, monoisotopic_mass=None, average_mass=None, dict_composition=None)
    lookup2 = OntologyLookup({"GG7": g}, "T", id_prefix="G")
    assert "g7" not in lookup2._index.by_exact_id  # "g7" normalizes to "7", not to GG7
    assert lookup2.query_id("g7") is None
    assert lookup2.query_id("GG7") is g


# --- lazy ontology imports --------------------------------------------------------------

_LAZY_MODULES = [
    "tacular.gno",
    "tacular.unimod",
    "tacular.psimod",
    "tacular.resid",
    "tacular.xlmod",
    "tacular.uniprot_ptm",
]


def _run(code: str) -> str:
    return subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True).stdout.strip()


def test_import_tacular_does_not_load_ontology_data():
    code = f"import sys, tacular; print([m for m in {_LAZY_MODULES!r} if m in sys.modules])"
    assert _run(code) == "[]"


def test_lazy_names_load_on_access():
    code = (
        "import sys, tacular\n"
        "assert tacular.GNO_LOOKUP['G00008BG'].id\n"
        "assert 'tacular.gno' in sys.modules and 'tacular.unimod' not in sys.modules\n"
        "from tacular import UNIMOD_LOOKUP, UnimodInfo\n"
        "assert isinstance(UNIMOD_LOOKUP['Phospho'], UnimodInfo)\n"
        "assert tacular.__dict__['UnimodLookup'] is type(UNIMOD_LOOKUP)\n"
        "print('ok')"
    )
    assert _run(code) == "ok"


def test_star_import_and_all_resolve():
    code = (
        "from tacular import *\n"
        "import tacular\n"
        "assert all(globals()[n] is getattr(tacular, n) for n in tacular.__all__)\n"
        "print(len(tacular.__all__))"
    )
    assert int(_run(code)) == len(t.__all__)


@pytest.mark.parametrize("module", [m.removeprefix("tacular.") for m in _LAZY_MODULES])
def test_lazy_subpackage_attribute_in_a_fresh_process(module):
    # Read the subpackage attribute first, before any of its names: on 1.x (eager
    # imports) ``tacular.unimod`` etc. were bound by ``import tacular``.
    code = (
        "import tacular\n"
        f"assert {module!r} in dir(tacular)\n"
        f"mod = tacular.{module}\n"
        f"assert mod.__name__ == 'tacular.{module}'\n"
        f"assert all(getattr(tacular, n) is getattr(mod, n) for n in tacular._LAZY_SUBMODULES[{module!r}])\n"
        "print('ok')"
    )
    assert _run(code) == "ok"


def test_lazy_module_getattr_and_dir():
    assert t.XLMOD_LOOKUP is t.xlmod.XLMOD_LOOKUP
    assert set(t.__all__) <= set(dir(t))
    with pytest.raises(AttributeError, match="no attribute 'NOT_A_LOOKUP'"):
        _ = t.NOT_A_LOOKUP  # type: ignore[attr-defined]


# --- query_mass(unit=) ------------------------------------------------------------------


def test_query_mass_ppm_is_a_relative_window():
    phospho = t.UNIMOD_LOOKUP["Phospho"]
    mass = phospho.monoisotopic_mass
    assert mass is not None
    near = mass * (1 + 5e-6)  # 5 ppm away
    assert phospho in t.UNIMOD_LOOKUP.query_mass(near, tolerance=10, unit="ppm")
    assert phospho not in t.UNIMOD_LOOKUP.query_mass(near, tolerance=2, unit="ppm")
    assert t.UNIMOD_LOOKUP.query_mass(near, tolerance=10, unit="ppm") == t.UNIMOD_LOOKUP.query_mass(
        near, tolerance=abs(near) * 10 / 1e6
    )
    assert t.UNIMOD_LOOKUP.query_mass(mass, unit="da") == t.UNIMOD_LOOKUP.query_mass(mass)


@settings(max_examples=200, deadline=None)
@given(
    lookup=st.sampled_from([*ONTOLOGY_LOOKUPS, _SYNTHETIC]),
    mass=st.one_of(_FLOATS, st.floats(min_value=-50, max_value=3000)),
    ppm=st.one_of(_FLOATS, st.floats(min_value=0, max_value=1000)),
    monoisotopic=st.booleans(),
)
def test_query_mass_ppm_matches_linear_scan(lookup, mass, ppm, monoisotopic):
    got = lookup.query_mass(mass, tolerance=ppm, unit="ppm", monoisotopic=monoisotopic)
    assert got == _query_mass_linear(lookup, mass, abs(mass) * ppm / 1e6, monoisotopic)


def test_query_mass_rejects_unknown_unit_and_positional_options():
    with pytest.raises(t.TacularError, match="unit"):
        t.UNIMOD_LOOKUP.query_mass(79.966, unit="mda")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        t.UNIMOD_LOOKUP.query_mass(79.966, 0.01)  # type: ignore[misc]


# --- OboEntity.composition cache --------------------------------------------------------

OBO_INFOS = [t.UNIMOD_LOOKUP["Phospho"], t.GNO_LOOKUP.choice(), t.MONOSACCHARIDE_LOOKUP["Hex"]]


@pytest.mark.parametrize("info", OBO_INFOS, ids=lambda i: type(i).__name__)
def test_obo_entity_composition_is_resolved_once_and_copied(info):
    first = info.composition
    resolved = info._resolved_composition
    second = info.composition
    assert info._resolved_composition is resolved
    assert type(first) is dict and first == second == t.parse_composition(info.dict_composition)
    assert first is not resolved and second is not first
    assert [str(k) for k in first] == list(info.dict_composition)  # key order kept
    first.clear()
    assert info.composition == resolved
    restored = pickle.loads(pickle.dumps(info))
    with pytest.raises(AttributeError):
        _ = restored._resolved_composition
    assert restored.composition == resolved
    assert "_resolved_composition" not in dataclasses.asdict(info)
    changed = dataclasses.replace(info, dict_composition={"C": 2})
    assert changed.composition == {t.ELEMENT_LOOKUP["C"]: 2}


def test_obo_entity_composition_none_and_bad_key():
    assert _entity(1, None).composition is None
    bad = OboEntity(
        id="1", name="bad", formula=None, monoisotopic_mass=None, average_mass=None, dict_composition={"Qq": 1}
    )
    for _ in range(2):  # a failed resolution is not cached
        with pytest.raises(t.TacularKeyError):
            _ = bad.composition


# --- read-only dict_composition ---------------------------------------------------------

READ_ONLY_INFOS = [*COMPOSITION_INFOS, t.AA_LOOKUP["G"], *OBO_INFOS]


@pytest.mark.parametrize("info", READ_ONLY_INFOS, ids=lambda i: type(i).__name__)
def test_dict_composition_is_read_only_so_the_cache_cannot_go_stale(info):
    import copy
    import json

    before = info.composition
    comp = info.dict_composition
    with pytest.raises(TypeError, match="read-only"):
        comp["C"] = 99
    for mutate in (
        lambda: comp.update(C=99),
        lambda: comp.pop("C"),
        lambda: comp.popitem(),
        lambda: comp.clear(),
        lambda: comp.setdefault("Zz", 1),
    ):
        with pytest.raises(TypeError):
            mutate()
    with pytest.raises(TypeError):
        del comp[next(iter(comp))]
    with pytest.raises(TypeError):
        comp |= {"C": 1}
    with pytest.raises(TypeError):
        comp.__init__({"C": 99})  # re-running the constructor must not refill it
    assert info.composition == before
    assert isinstance(comp, dict) and comp == dict(comp)
    assert json.loads(json.dumps(comp)) == dict(comp)
    for clone in (pickle.loads(pickle.dumps(info)), copy.copy(info), copy.deepcopy(info), dataclasses.replace(info)):
        assert clone == info
        assert clone.dict_composition == comp
        assert type(clone.dict_composition) is type(comp)
        assert clone.composition == before
    assert dataclasses.asdict(info)["dict_composition"] == dict(comp)


def test_dict_composition_input_is_copied():
    source = {"H": 2, "O": 1}
    e = OboEntity(id="1", name="w", formula=None, monoisotopic_mass=None, average_mass=None, dict_composition=source)
    assert e.dict_composition is not source
    source["H"] = 5  # the caller's dict stays theirs
    assert e.dict_composition == {"H": 2, "O": 1}
    assert e.composition == {t.ELEMENT_LOOKUP["H"]: 2, t.ELEMENT_LOOKUP["O"]: 1}
    frozen = e.dict_composition
    assert dataclasses.replace(e).dict_composition is frozen  # already read-only: not re-copied


def test_query_mass_nan_returns_empty():
    assert t.UNIMOD_LOOKUP.query_mass(math.nan) == []
    assert t.UNIMOD_LOOKUP.query_mass(79.966, tolerance=math.nan) == []
    assert t.UNIMOD_LOOKUP.query_mass(math.inf, tolerance=0, unit="ppm") == []


def test_read_only_dict_refuses_a_second_init_even_when_empty():
    from tacular._util import _ReadOnlyDict

    empty = _ReadOnlyDict()
    with pytest.raises(TypeError):
        empty.__init__({"C": 1})
    assert empty == {}
    import copy
    import pickle

    full = _ReadOnlyDict({"C": 2})
    assert copy.deepcopy(full) == pickle.loads(pickle.dumps(full)) == {"C": 2}
