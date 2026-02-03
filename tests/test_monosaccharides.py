import pytest

from tacular import MONOSACCHARIDE_LOOKUP as db


class TestMonosaccharideLookupBasics:
    """Test basic monosaccharide lookup operations"""

    def test_getitem_by_proforma_name(self):
        """Test __getitem__ with ProForma names"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            # Get by ProForma name (case insensitive)
            result = db[first_entry.name]
            assert result.name.lower() == first_entry.name.lower()

    def test_contains(self):
        """Test __contains__ operator"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            assert first_entry.name in db
            assert first_entry.name.lower() in db
            assert first_entry.name.upper() in db
        assert "NotAMonosaccharide" not in db

    def test_iter(self):
        """Test iteration over monosaccharides"""
        entries = list(db)
        assert len(entries) > 0
        # All should have names
        for entry in entries:
            assert entry.name is not None

    def test_get_with_default(self):
        """Test get() method with default value"""
        result = db.get("NonexistentMonosaccharide")
        assert result is None

    def test_case_insensitivity(self):
        """Test case-insensitive lookups"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            lower = db.get(first_entry.name.lower())
            upper = db.get(first_entry.name.upper())
            mixed = db.get(first_entry.name)

            assert lower is not None
            assert upper is not None
            assert mixed is not None
            # All should reference the same object
            assert lower is upper
            assert lower is mixed


class TestMonosaccharideLookupQueryMethods:
    """Test monosaccharide query methods"""

    def test_proforma_method(self):
        """Test proforma() method"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db.proforma(first_entry.name)
            assert result is not None
            assert result.name.lower() == first_entry.name.lower()

    def test_proforma_not_found(self):
        """Test proforma() with non-existent name raises KeyError"""
        with pytest.raises(KeyError):
            db.proforma("NonExistentMonosaccharide")

    def test_proforma_case_insensitive(self):
        """Test proforma() is case insensitive"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            lower = db.proforma(first_entry.name.lower())
            upper = db.proforma(first_entry.name.upper())
            assert lower is upper


class TestMonosaccharideEdgeCases:
    """Test edge cases and error handling"""

    def test_getitem_not_found(self):
        """Test __getitem__ with non-existent key raises KeyError"""
        with pytest.raises(KeyError):
            _ = db["NonExistentMonosaccharide"]

    def test_empty_string_lookup(self):
        """Test lookup with empty string"""
        result = db.get("")
        assert result is None

    def test_contains_empty_string(self):
        """Test __contains__ with empty string"""
        assert "" not in db


class TestMonosaccharideDataIntegrity:
    """Test data integrity for monosaccharides"""

    def test_all_entries_have_names(self):
        """Test all entries have non-empty names"""
        for entry in db:
            assert entry.name is not None
            assert len(entry.name) > 0

    def test_all_entries_have_ids(self):
        """Test all entries have IDs"""
        for entry in db:
            assert entry.id is not None

    def test_masses_when_defined(self):
        """Test masses are positive when defined"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                assert entry.monoisotopic_mass > 0
            if entry.average_mass is not None:
                assert entry.average_mass > 0

    def test_common_monosaccharides_exist(self):
        """Test that some common monosaccharides exist"""
        # Common monosaccharides in glycobiology
        common = ["Hex", "HexNAc", "Neu", "NeuAc", "NeuGc", "Glc", "Gal", "Man", "Fuc"]
        found_count = 0
        for name in common:
            if name in db:
                found_count += 1
        # At least some common ones should exist
        assert found_count > 0

    def test_lookup_consistency(self):
        """Test that multiple lookups return the same object"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result1 = db[first_entry.name]
            result2 = db[first_entry.name]
            assert result1 is result2

    def test_iteration_stable(self):
        """Test iteration order is stable"""
        list1 = [e.name for e in db]
        list2 = [e.name for e in db]
        assert list1 == list2

    def test_formulas_when_defined(self):
        """Test formulas are non-empty when defined"""
        for entry in db:
            if entry.formula is not None:
                assert len(entry.formula) > 0
                # Should contain at least one letter (element symbol)
                assert any(c.isalpha() for c in entry.formula)
                break  # Just check a few


if __name__ == "__main__":
    pytest.main([__file__])
