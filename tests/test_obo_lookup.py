from types import MappingProxyType

import pytest

from tacular.obo_entity import OboEntity
from tacular.obo_lookup import OntologyLookup


def make_entity(id, name, mass=None, avg=None, comp=None):
    return OboEntity(
        id=id,
        name=name,
        formula=None,
        monoisotopic_mass=mass,
        average_mass=avg,
        dict_composition=MappingProxyType(comp) if comp else None,
    )


def test_query_id_and_name():
    e1 = make_entity("1", "A")
    e2 = make_entity("2", "B")
    lookup = OntologyLookup({e1.id: e1, e2.id: e2}, "TEST")
    assert lookup.query_id("1") is e1
    assert lookup.query_id(1) is e1
    assert lookup.query_name("A") is e1
    assert lookup.get("B") is e2
    assert lookup.get("2") is e2
    assert lookup.get("notfound") is None
    with pytest.raises(KeyError):
        _ = lookup["notfound"]
    assert "A" in lookup
    assert "1" in lookup
    assert "notfound" not in lookup


def test_query_mass():
    e1 = make_entity("1", "A", mass=10.0)
    e2 = make_entity("2", "B", mass=10.005)
    lookup = OntologyLookup({e1.id: e1, e2.id: e2}, "TEST")
    # Reduced tolerance to avoid overlap
    assert lookup.query_mass(10.0, tolerance=0.002) is e1
    assert lookup.query_mass(10.005, tolerance=0.002) is e2
    # Multiple matches with same composition
    e3 = make_entity("3", "C", mass=10.0, comp={"H": 2})
    e4 = make_entity("4", "D", mass=10.0, comp={"H": 2})
    lookup2 = OntologyLookup({e3.id: e3, e4.id: e4}, "TEST")
    assert lookup2.query_mass(10.0, tolerance=0.01) in (e3, e4)
    # Multiple matches with different composition
    e5 = make_entity("5", "E", mass=10.0, comp={"H": 1})
    lookup3 = OntologyLookup({e3.id: e3, e5.id: e5}, "TEST")
    with pytest.raises(ValueError):
        lookup3.query_mass(10.0, tolerance=0.01)
    assert lookup.query_mass(99.0, tolerance=0.01) is None


def test_iter_and_values_keys():
    e1 = make_entity("1", "A")
    e2 = make_entity("2", "B")
    lookup = OntologyLookup({e1.id: e1, e2.id: e2}, "TEST")
    names = set([x.name for x in lookup])
    assert names == {"A", "B"}
    assert set(lookup.values()) == set([e1, e2])
    assert set(lookup.keys()) == {"a", "b"}


def test_choice():
    e1 = make_entity("1", "A", mass=1.0, comp={"H": 2})
    e2 = make_entity("2", "B", mass=2.0, comp={"H": 1})
    lookup = OntologyLookup({e1.id: e1, e2.id: e2}, "TEST")
    # Should always return one of the two
    for _ in range(10):
        assert lookup.choice() in (e1, e2)
    # If no valid entries, raises
    lookup_empty = OntologyLookup({}, "TEST")
    with pytest.raises(ValueError):
        lookup_empty.choice()


def test_query_id_integer():
    e1 = make_entity("123", "A")
    lookup = OntologyLookup({e1.id: e1}, "TEST")
    assert lookup.query_id(123) is e1


def test_query_mass_not_monoisotopic():
    e1 = make_entity("1", "A", mass=10.0, avg=10.5)
    lookup = OntologyLookup({e1.id: e1}, "TEST")
    # Query monoisotopic (default)
    assert lookup.query_mass(10.0, tolerance=0.01) is e1
    assert lookup.query_mass(10.5, tolerance=0.01) is None

    # Query average
    assert lookup.query_mass(10.5, tolerance=0.01, monoisotopic=False) is e1
    assert lookup.query_mass(10.0, tolerance=0.01, monoisotopic=False) is None


def test_choice_compositions():
    # Setup entries with/without mass/composition
    e_full = make_entity("1", "Full", mass=10.0, comp={"H": 1})
    e_mass = make_entity("2", "MassOnly", mass=20.0, comp=None)
    e_comp = make_entity("3", "CompOnly", mass=None, comp={"O": 1})
    e_none = make_entity("4", "None", mass=None, comp=None)

    lookup = OntologyLookup({e_full.id: e_full, e_mass.id: e_mass, e_comp.id: e_comp, e_none.id: e_none}, "TEST")

    # Default: requires mass and comp
    for _ in range(10):
        assert lookup.choice() == e_full

    # Require mass only
    for _ in range(20):
        res = lookup.choice(require_composition=False)
        assert res in (e_full, e_mass)

    # Require comp only
    for _ in range(20):
        res = lookup.choice(require_monoisotopic_mass=False)
        assert res in (e_full, e_comp)

    # No requirements
    for _ in range(50):
        res = lookup.choice(require_monoisotopic_mass=False, require_composition=False)
        assert res in (e_full, e_mass, e_comp, e_none)
