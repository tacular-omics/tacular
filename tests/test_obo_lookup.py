from types import MappingProxyType

import pytest

import tacular as t
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
    assert e1 in lookup.query_mass(10.0, tolerance=0.002)
    assert e2 in lookup.query_mass(10.005, tolerance=0.002)
    # Multiple matches with same composition
    e3 = make_entity("3", "C", mass=10.0, comp={"H": 2})
    e4 = make_entity("4", "D", mass=10.0, comp={"H": 2})
    lookup2 = OntologyLookup({e3.id: e3, e4.id: e4}, "TEST")
    assert e3 in lookup2.query_mass(10.0, tolerance=0.01)
    assert e4 in lookup2.query_mass(10.0, tolerance=0.01)
    assert lookup.query_mass(99.0, tolerance=0.01) == []


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
    assert e1 in lookup.query_mass(10.0, tolerance=0.01)
    assert len(lookup.query_mass(10.5, tolerance=0.01)) == 0

    # Query average
    assert e1 in lookup.query_mass(10.5, tolerance=0.01, monoisotopic=False)
    assert len(lookup.query_mass(10.0, tolerance=0.01, monoisotopic=False)) == 0


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


def test_lookup_UNIMOD():
    assert 1 in t.UNIMOD_LOOKUP
    assert "1" in t.UNIMOD_LOOKUP
    assert "0001" in t.UNIMOD_LOOKUP
    assert "Acetyl" in t.UNIMOD_LOOKUP
    assert "aceTyl" in t.UNIMOD_LOOKUP

def test_lookup_RESID():
    assert 2 in t.RESID_LOOKUP
    assert "2" in t.RESID_LOOKUP
    assert "0002" in t.RESID_LOOKUP
    assert "AA0002" in t.RESID_LOOKUP
    assert "AA2" in t.RESID_LOOKUP
    assert "L-arginine residue" in t.RESID_LOOKUP
    assert "l-Arginine ReSidue" in t.RESID_LOOKUP


def test_lookup_GNO():
    assert "8BG" in t.GNO_LOOKUP
    assert "G00008BG" in t.GNO_LOOKUP
    assert "G008BG" in t.GNO_LOOKUP
    assert "G00008BG" in t.GNO_LOOKUP
    assert "G00008bg" in t.GNO_LOOKUP


class TestUnimodLookupComprehensive:
    """Comprehensive tests for UNIMOD_LOOKUP"""

    def test_query_id_variations(self):
        """Test various ID formats for UNIMOD"""
        # Acetyl is ID 1
        acetyl = t.UNIMOD_LOOKUP.query_id("1")
        assert acetyl is not None
        assert acetyl.name == "Acetyl"

        # Same with zero-padded
        assert t.UNIMOD_LOOKUP.query_id("0001") is acetyl
        # Integer
        assert t.UNIMOD_LOOKUP.query_id(1) is acetyl

    def test_query_name_case_insensitive(self):
        """Test case-insensitive name queries"""
        acetyl_lower = t.UNIMOD_LOOKUP.query_name("acetyl")
        acetyl_upper = t.UNIMOD_LOOKUP.query_name("ACETYL")
        acetyl_mixed = t.UNIMOD_LOOKUP.query_name("AceTyl")

        assert acetyl_lower is not None
        assert acetyl_lower is acetyl_upper
        assert acetyl_lower is acetyl_mixed

    def test_query_mass(self):
        """Test mass-based queries"""
        # Acetyl mass is approximately 42.01
        results = t.UNIMOD_LOOKUP.query_mass(42.01, tolerance=0.1)
        assert len(results) > 0
        # Check Acetyl is in results
        assert any(r.name == "Acetyl" for r in results)

    def test_iteration(self):
        """Test iteration over all entries"""
        entries = list(t.UNIMOD_LOOKUP)
        assert len(entries) > 100  # UNIMOD has many entries
        # All should have IDs and names
        for entry in entries:
            assert entry.id is not None
            assert entry.name is not None

    def test_data_integrity(self):
        """Test data integrity of UNIMOD entries"""
        acetyl = t.UNIMOD_LOOKUP["Acetyl"]
        assert acetyl.monoisotopic_mass is not None
        assert acetyl.monoisotopic_mass > 0
        # Should have reasonable mass
        assert 40 < acetyl.monoisotopic_mass < 50


class TestResidLookupComprehensive:
    """Comprehensive tests for RESID_LOOKUP"""

    def test_query_id_prefix_stripping(self):
        """Test RESID prefix stripping (AA prefix)"""
        # RESID IDs have AA prefix
        if len(list(t.RESID_LOOKUP)) > 0:
            first_entry = next(iter(t.RESID_LOOKUP))
            # Try various formats
            numeric_id = first_entry.id_tag
            result1 = t.RESID_LOOKUP.query_id(numeric_id)
            result2 = t.RESID_LOOKUP.query_id(f"AA{numeric_id}")
            result3 = t.RESID_LOOKUP.query_id(first_entry.id)

            assert result1 is result2
            assert result1 is result3

    def test_query_name_amino_acids(self):
        """Test querying known amino acid residues"""
        # Test L-arginine residue if it exists
        arg_result = t.RESID_LOOKUP.query_name("L-arginine residue")
        if arg_result:
            assert arg_result.name is not None
            # Case insensitive
            assert t.RESID_LOOKUP.query_name("l-ARGININE residue") is arg_result

    def test_contains_various_formats(self):
        """Test __contains__ with various ID formats"""
        assert "2" in t.RESID_LOOKUP
        assert "0002" in t.RESID_LOOKUP
        assert "AA0002" in t.RESID_LOOKUP
        assert "AA2" in t.RESID_LOOKUP

    def test_iteration(self):
        """Test iteration over RESID entries"""
        entries = list(t.RESID_LOOKUP)
        assert len(entries) > 0
        # All should have IDs and names
        for entry in entries:
            assert entry.id is not None
            assert entry.name is not None

    def test_mass_queries(self):
        """Test mass-based queries for RESID"""
        # Get first entry with mass
        for entry in t.RESID_LOOKUP:
            if entry.monoisotopic_mass is not None:
                results = t.RESID_LOOKUP.query_mass(
                    entry.monoisotopic_mass,
                    tolerance=0.01
                )
                assert len(results) > 0
                assert any(r.id == entry.id for r in results)
                break

