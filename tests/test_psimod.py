import pytest

from tacular import PSIMOD_LOOKUP as db


class TestPsimodLookupBasics:
    """Test basic PSIMOD lookup operations"""

    def test_getitem_by_id(self):
        """Test __getitem__ with IDs"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db[first_entry.id]
            assert result.id == first_entry.id
            assert result.name is not None

    def test_contains(self):
        """Test __contains__ operator"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            assert first_entry.id in db
            assert first_entry.name in db
        assert "NotAModification" not in db
        assert "INVALID" not in db

    def test_iter(self):
        """Test iteration over PSIMOD entries"""
        entries = list(db)
        assert len(entries) > 0
        for entry in entries:
            assert entry.id is not None
            assert entry.name is not None

    def test_get_with_default(self):
        """Test get() method with default value"""
        result = db.get("NonexistentEntry", default=None)
        assert result is None

    def test_len(self):
        """Test __len__ returns correct count"""
        length = len(db)
        assert length > 0
        assert length == len(list(db))


class TestPsimodLookupQueryMethods:
    """Test PSIMOD query methods"""

    def test_query_id_numeric(self):
        """Test query_id with numeric IDs"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db.query_id(first_entry.id)
            assert result.id == first_entry.id
            # Try with stripped zeros if applicable
            try:
                int_id = int(first_entry.id)
                result = db.query_id(str(int_id))
                assert result is not None
            except ValueError:
                pass

    def test_query_id_not_found(self):
        """Test query_id with non-existent ID"""
        result = db.query_id("99999")
        assert result is None

    def test_query_name(self):
        """Test query_name with case insensitivity"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db.query_name(first_entry.name)
            assert result is not None
            assert result.name.lower() == first_entry.name.lower()

            # Try with different case
            result_upper = db.query_name(first_entry.name.upper())
            assert result_upper is not None
            result_lower = db.query_name(first_entry.name.lower())
            assert result_lower is not None

    def test_query_name_not_found(self):
        """Test query_name with non-existent name"""
        result = db.query_name("NonExistentModificationName")
        assert result is None

    def test_query_mass_monoisotopic(self):
        """Test query_mass with monoisotopic masses"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                mass = entry.monoisotopic_mass
                results = db.query_mass(mass, tolerance=0.01, monoisotopic=True)
                assert len(results) > 0
                assert any(r.id == entry.id for r in results)
                break

    def test_query_mass_average(self):
        """Test query_mass with average masses"""
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

    def test_query_mass_tolerance(self):
        """Test query_mass with different tolerances"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                mass = entry.monoisotopic_mass
                # Tight tolerance
                results_tight = db.query_mass(mass, tolerance=0.001, monoisotopic=True)
                # Loose tolerance
                results_loose = db.query_mass(mass, tolerance=1.0, monoisotopic=True)
                # Loose should have at least as many results
                assert len(results_loose) >= len(results_tight)
                break


class TestPsimodSpecialFeatures:
    """Test PSIMOD special features like choice() and filtering"""

    def test_choice_random_selection(self):
        """Test choice() returns random entry"""
        if len(list(db)) > 1:
            # Call multiple times, should work without error
            choice1 = db.choice()
            assert choice1 is not None
            assert choice1.id is not None

            choice2 = db.choice()
            assert choice2 is not None


    def test_getitem_tries_name_then_id(self):
        """Test __getitem__ tries name first, then ID"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            # By name
            result = db[first_entry.name]
            assert result.name.lower() == first_entry.name.lower()
            # By ID
            result = db[first_entry.id]
            assert result.id == first_entry.id


class TestPsimodEdgeCases:
    """Test edge cases and error handling"""

    def test_getitem_not_found(self):
        """Test __getitem__ with non-existent key raises KeyError"""
        with pytest.raises(KeyError):
            _ = db["NonExistentModKey"]

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
        # Some modifications may have negative masses (losses)
        # Just ensure it returns a list
        assert isinstance(results, list)

    def test_query_mass_zero_tolerance(self):
        """Test query_mass with zero tolerance"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                results = db.query_mass(entry.monoisotopic_mass, tolerance=0.0, monoisotopic=True)
                # Should still find at least the exact match
                assert len(results) > 0
                break


class TestPsimodDataIntegrity:
    """Test data integrity for PSIMOD entries"""

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

    def test_masses_are_reasonable(self):
        """Test all defined masses are reasonable"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                # Should be within reasonable range for modifications
                assert abs(entry.monoisotopic_mass) < 10000
            if entry.average_mass is not None:
                assert abs(entry.average_mass) < 10000

    def test_id_name_lookup_consistency(self):
        """Test that ID and name lookups return same object"""
        count_checked = 0
        for entry in db:
            by_id = db.query_id(entry.id)
            by_name = db.query_name(entry.name)
            assert by_id is by_name
            count_checked += 1
            if count_checked >= 10:
                break

    def test_mass_query_returns_correct_entries(self):
        """Test mass queries return entries within tolerance"""
        for entry in db:
            if entry.monoisotopic_mass is not None:
                tolerance = 0.01
                results = db.query_mass(entry.monoisotopic_mass, tolerance=tolerance, monoisotopic=True)
                for result in results:
                    if result.monoisotopic_mass is not None:
                        assert abs(result.monoisotopic_mass - entry.monoisotopic_mass) <= tolerance
                break

    def test_no_duplicate_ids(self):
        """Test there are no duplicate IDs"""
        ids = [entry.id for entry in db]
        assert len(ids) == len(set(ids))

    def test_iteration_order_stable(self):
        """Test iteration order is stable across calls"""
        list1 = list(db)
        list2 = list(db)
        assert [e.id for e in list1] == [e.id for e in list2]
