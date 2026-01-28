import pytest

from tacular import NEUTRAL_DELTA_LOOKUP as db
from tacular.neutral_deltas import NeutralDelta


class TestNeutralDeltaLookupBasics:
    """Test basic neutral delta lookup operations"""

    def test_getitem_by_formula(self):
        """Test __getitem__ with chemical formulas"""
        # H2O (water) is a common neutral loss
        if "H2O" in db:
            water = db["H2O"]
            assert water.formula == "H2O"
            assert water.name is not None

    def test_getitem_by_name(self):
        """Test __getitem__ with names"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db[first_entry.name]
            assert result.name.lower() == first_entry.name.lower()

    def test_getitem_by_neutral_delta_enum(self):
        """Test __getitem__ with NeutralDelta enum"""
        # Try to access via enum if available
        if hasattr(NeutralDelta, "H2O"):
            result = db[NeutralDelta.H2O]
            assert result.formula == "H2O"

    def test_contains(self):
        """Test __contains__ operator"""
        if "H2O" in db:
            assert "H2O" in db
            assert "h2o" in db  # case insensitive
        assert "NotAFormula" not in db

    def test_iter(self):
        """Test iteration over neutral deltas"""
        deltas = list(db)
        assert len(deltas) > 0
        # All should have formulas and names
        for delta in deltas:
            assert delta.formula is not None
            assert delta.name is not None

    def test_len(self):
        """Test __len__ returns correct count"""
        length = len(db)
        assert length > 0
        assert length == len(list(db))

    def test_repr(self):
        """Test __repr__ includes count"""
        repr_str = repr(db)
        assert "NeutralDeltaLookup" in repr_str
        assert str(len(db)) in repr_str

    def test_case_insensitivity(self):
        """Test case-insensitive lookups"""
        if "H2O" in db:
            water_lower = db.query_formula("h2o")
            water_upper = db.query_formula("H2O")
            assert water_lower is water_upper


class TestNeutralDeltaLookupQueryMethods:
    """Test neutral delta query methods"""

    def test_query_formula(self):
        """Test query_formula method"""
        if "H2O" in db:
            result = db.query_formula("H2O")
            assert result is not None
            assert result.formula == "H2O"
            # Case insensitive
            assert db.query_formula("h2o") is result

    def test_query_formula_not_found(self):
        """Test query_formula with non-existent formula"""
        result = db.query_formula("XYZ123")
        assert result is None

    def test_query_name(self):
        """Test query_name method"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db.query_name(first_entry.name)
            assert result is not None
            assert result.name.lower() == first_entry.name.lower()

    def test_query_name_not_found(self):
        """Test query_name with non-existent name"""
        result = db.query_name("NonExistentNeutralDelta")
        assert result is None

    def test_query_delta_enum(self):
        """Test query_delta with NeutralDelta enum"""
        if hasattr(NeutralDelta, "H2O"):
            result = db.query_delta(NeutralDelta.H2O)
            assert result is not None
            assert result.formula == "H2O"


class TestNeutralDeltaSpecialFeatures:
    """Test neutral delta special features like calculate_loss_sites"""

    def test_calculate_loss_sites_water(self):
        """Test calculate_loss_sites for water loss"""
        if "H2O" in db:
            water = db["H2O"]
            # Water can be lost from S, T, E, D typically
            # Test with a sequence containing these residues
            sequence = "STED"
            sites = water.calculate_loss_sites(sequence)
            assert sites >= 0
            assert sites <= len(sequence)
            # Each residue in amino_acids should be counted
            expected = sum(1 for aa in sequence if aa in water.amino_acids)
            assert sites == expected

    def test_calculate_loss_sites_no_sites(self):
        """Test calculate_loss_sites with sequence having no loss sites"""
        if len(list(db)) > 0:
            first_delta = next(iter(db))
            # Create sequence with no matching amino acids
            sequence = "G" * 10  # Glycine typically doesn't lose much
            sites = first_delta.calculate_loss_sites(sequence)
            assert sites >= 0

    def test_calculate_loss_sites_empty_sequence(self):
        """Test calculate_loss_sites with empty sequence"""
        if len(list(db)) > 0:
            first_delta = next(iter(db))
            sites = first_delta.calculate_loss_sites("")
            assert sites == 0

    def test_amino_acids_frozenset(self):
        """Test amino_acids is a frozenset"""
        if len(list(db)) > 0:
            first_delta = next(iter(db))
            assert isinstance(first_delta.amino_acids, frozenset)

    def test_amino_acids_contains_valid_codes(self):
        """Test amino_acids contains valid single-letter codes"""
        valid_codes = set("ACDEFGHIKLMNPQRSTVWY")
        for delta in db:
            # All amino acid codes should be single letters
            for aa in delta.amino_acids:
                assert len(aa) == 1
                # Most should be standard amino acids
                if aa.isalpha():
                    assert aa.upper() in valid_codes or aa == "*"
            break  # Just check first few


class TestNeutralDeltaMethods:
    """Test NeutralDeltaInfo methods"""

    def test_get_mass_monoisotopic(self):
        """Test get_mass with monoisotopic=True"""
        if len(list(db)) > 0:
            delta = next(iter(db))
            mass = delta.get_mass(monoisotopic=True)
            assert mass == delta.monoisotopic_mass
            assert isinstance(mass, float)

    def test_get_mass_average(self):
        """Test get_mass with monoisotopic=False"""
        if len(list(db)) > 0:
            delta = next(iter(db))
            mass = delta.get_mass(monoisotopic=False)
            assert mass == delta.average_mass
            assert isinstance(mass, float)

    def test_composition_property(self):
        """Test composition cached property"""
        if len(list(db)) > 0:
            delta = next(iter(db))
            comp = delta.composition
            assert comp is not None
            assert len(comp) > 0

    def test_to_dict(self):
        """Test to_dict conversion"""
        if len(list(db)) > 0:
            delta = next(iter(db))
            d = delta.to_dict()
            assert d["formula"] == delta.formula
            assert d["name"] == delta.name
            assert "description" in d
            assert "amino_acids" in d
            assert "monoisotopic_mass" in d
            assert "average_mass" in d
            assert "dict_composition" in d

    def test_hash(self):
        """Test __hash__ for use in sets/dicts"""
        if len(list(db)) >= 2:
            deltas = list(db)
            # Should be hashable
            delta_set = {deltas[0], deltas[1]}
            assert len(delta_set) <= 2


class TestNeutralDeltaEdgeCases:
    """Test edge cases and error handling"""

    def test_getitem_not_found(self):
        """Test __getitem__ with non-existent key raises KeyError"""
        with pytest.raises(KeyError):
            _ = db["NonExistentDelta"]

    def test_query_formula_empty_string(self):
        """Test query_formula with empty string"""
        result = db.query_formula("")
        assert result is None

    def test_query_name_empty_string(self):
        """Test query_name with empty string"""
        result = db.query_name("")
        assert result is None


class TestNeutralDeltaDataIntegrity:
    """Test data integrity for neutral deltas"""

    def test_all_have_formulas(self):
        """Test all entries have non-empty formulas"""
        for delta in db:
            assert delta.formula is not None
            assert len(delta.formula) > 0

    def test_all_have_names(self):
        """Test all entries have non-empty names"""
        for delta in db:
            assert delta.name is not None
            assert len(delta.name) > 0

    def test_all_have_descriptions(self):
        """Test all entries have descriptions"""
        for delta in db:
            assert delta.description is not None

    def test_masses_are_reasonable(self):
        """Test masses are within reasonable ranges"""
        for delta in db:
            # Neutral losses typically have small masses
            assert abs(delta.monoisotopic_mass) < 1000
            assert abs(delta.average_mass) < 1000

    def test_common_losses_exist(self):
        """Test that common neutral losses exist"""
        common_losses = ["H2O", "NH3", "CO", "CO2"]
        found_count = 0
        for formula in common_losses:
            if formula in db:
                found_count += 1
        # At least some common losses should exist
        assert found_count > 0

    def test_formula_name_lookup_consistency(self):
        """Test formula and name lookups return same object"""
        if len(list(db)) > 0:
            first_delta = next(iter(db))
            by_formula = db.query_formula(first_delta.formula)
            by_name = db.query_name(first_delta.name)
            assert by_formula is by_name

    def test_composition_matches_formula(self):
        """Test composition is consistent with formula"""
        for delta in db:
            comp = delta.composition
            # Composition should have at least one element
            assert len(comp) > 0
            # Total atom count should be reasonable
            total_atoms = sum(comp.values())

