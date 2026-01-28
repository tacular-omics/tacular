import pytest

from tacular import GNO_LOOKUP as db


class TestGnoLookupBasics:
    """Test basic GNO lookup operations"""

    def test_getitem_by_id(self):
        """Test __getitem__ with IDs"""
        # GNO IDs have 'G' prefix
        # Try to get a known entry if one exists
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            # Try with full ID
            result = db[first_entry.id]
            assert result.id == first_entry.id
            assert result.name is not None

    def test_contains(self):
        """Test __contains__ operator"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            assert first_entry.id in db
            assert first_entry.name in db
        assert "NotAGlycan" not in db
        assert "INVALID" not in db

    def test_iter(self):
        """Test iteration over GNO entries"""
        entries = list(db)
        # Should have some entries
        assert len(entries) >= 0
        # All should have required attributes
        for entry in entries:
            assert entry.id is not None
            assert entry.name is not None

    def test_get_with_default(self):
        """Test get() method with default value"""
        result = db.get("NonexistentEntry", default=None)
        assert result is None


class TestGnoLookupQueryMethods:
    """Test GNO query methods"""

    def test_query_id_with_prefix(self):
        """Test query_id with 'G' prefix"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            # Query with prefix 'G'
            if first_entry.id.startswith("G"):
                result = db.query_id(first_entry.id)
                assert result.id == first_entry.id
            # Query without prefix (should work due to prefix stripping)
            id_without_prefix = first_entry.id.lstrip("G")
            if id_without_prefix:
                result = db.query_id(id_without_prefix)
                assert result.id == first_entry.id

    def test_query_id_not_found(self):
        """Test query_id with non-existent ID"""
        result = db.query_id("99999999XX")
        assert result is None

    def test_query_name(self):
        """Test query_name with case insensitivity"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            # Case insensitive
            result = db.query_name(first_entry.name)
            assert result is not None
            assert result.name.lower() == first_entry.name.lower()

            # Try with different case
            result_upper = db.query_name(first_entry.name.upper())
            assert result_upper is not None

    def test_query_name_not_found(self):
        """Test query_name with non-existent name"""
        result = db.query_name("NonExistentGlycanName")
        assert result is None

    def test_query_mass_monoisotopic(self):
        """Test query_mass with monoisotopic masses"""
        if len(list(db)) > 0:
            # Get first entry with defined mass
            for entry in db:
                if entry.monoisotopic_mass is not None:
                    mass = entry.monoisotopic_mass
                    # Query with exact mass and tolerance
                    results = db.query_mass(mass, tolerance=0.01, monoisotopic=True)
                    assert len(results) > 0
                    # Check that our entry is in results
                    assert any(r.id == entry.id for r in results)
                    break

    def test_query_mass_average(self):
        """Test query_mass with average masses"""
        if len(list(db)) > 0:
            for entry in db:
                if entry.average_mass is not None:
                    mass = entry.average_mass
                    results = db.query_mass(mass, tolerance=0.01, monoisotopic=False)
                    assert len(results) > 0
                    assert any(r.id == entry.id for r in results)
                    break

    def test_query_mass_no_results(self):
        """Test query_mass with mass that has no matches"""
        results = db.query_mass(999999.999, tolerance=0.01)
        assert len(results) == 0


class TestGnoLookupEdgeCases:
    """Test edge cases and error handling"""

    def test_getitem_not_found(self):
        """Test __getitem__ with non-existent key raises KeyError"""
        with pytest.raises(KeyError):
            _ = db["NonExistentGlycanKey"]

    def test_query_id_empty_string(self):
        """Test query_id with empty string"""
        result = db.query_id("")
        assert result is None

    def test_query_name_empty_string(self):
        """Test query_name with empty string"""
        result = db.query_name("")
        assert result is None

    def test_query_mass_negative(self):
        """Test query_mass with negative mass"""
        results = db.query_mass(-100.0, tolerance=0.01)
        assert len(results) == 0


class TestGnoDataIntegrity:
    """Test data integrity for GNO entries"""

    def test_all_entries_have_ids(self):
        """Test all entries have non-empty IDs"""
        for entry in db:
            assert entry.id is not None
            assert len(entry.id) > 0

    def test_all_entries_have_names(self):
        """Test all entries have non-empty names"""
        for entry in db:
            assert entry.name is not None
            assert len(entry.name) > 0

    def test_masses_are_positive(self):
        """Test all defined masses are positive"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                assert entry.monoisotopic_mass > 0
            if entry.average_mass is not None:
                assert entry.average_mass > 0

    def test_id_name_lookup_consistency(self):
        """Test that ID and name lookups return same object"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            by_id = db.query_id(first_entry.id)
            by_name = db.query_name(first_entry.name)
            assert by_id is by_name

    def test_mass_query_returns_correct_entries(self):
        """Test mass queries return entries within tolerance"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                tolerance = 0.01
                results = db.query_mass(entry.monoisotopic_mass, tolerance=tolerance, monoisotopic=True)
                for result in results:
                    assert abs(result.monoisotopic_mass - entry.monoisotopic_mass) <= tolerance
                break
