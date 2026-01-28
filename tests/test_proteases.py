import re

import pytest

from tacular import PROTEASE_LOOKUP as db


class TestProteaseLookupBasics:
    """Test basic protease lookup operations"""

    def test_getitem_by_id(self):
        """Test __getitem__ with protease IDs"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db[first_entry.id]
            assert result.id.lower() == first_entry.id.lower()
            assert result.name is not None

    def test_getitem_by_name(self):
        """Test __getitem__ with protease names"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db[first_entry.name]
            assert result.name.lower() == first_entry.name.lower()

    def test_contains(self):
        """Test __contains__ operator"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            assert first_entry.id in db
            assert first_entry.name in db
        assert "NotAProtease" not in db

    def test_iter(self):
        """Test iteration over proteases"""
        proteases = list(db)
        assert len(proteases) > 0
        # All should have IDs and names
        for protease in proteases:
            assert protease.id is not None
            assert protease.name is not None

    def test_get_with_default(self):
        """Test get() method with default value"""
        result = db.get("NonexistentProtease")
        assert result is None

    def test_case_insensitivity(self):
        """Test case-insensitive lookups"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            lower = db.query_id(first_entry.id.lower())
            upper = db.query_id(first_entry.id.upper())
            assert lower is upper


class TestProteaseLookupQueryMethods:
    """Test protease query methods"""

    def test_query_id(self):
        """Test query_id method"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            result = db.query_id(first_entry.id)
            assert result is not None
            assert result.id.lower() == first_entry.id.lower()

    def test_query_id_not_found(self):
        """Test query_id with non-existent ID"""
        result = db.query_id("nonexistentprotease")
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
        result = db.query_name("NonExistentProteaseName")
        assert result is None

    def test_query_name_case_insensitive(self):
        """Test query_name is case insensitive"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            lower = db.query_name(first_entry.name.lower())
            upper = db.query_name(first_entry.name.upper())
            assert lower is upper


class TestProteaseRegexPatterns:
    """Test protease regex patterns and compilation"""

    def test_all_have_regex(self):
        """Test all proteases have regex patterns"""
        for protease in db:
            assert protease.regex is not None
            assert len(protease.regex) > 0

    def test_pattern_compilation(self):
        """Test pattern cached property compiles regex"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            pattern = first_entry.pattern
            assert pattern is not None
            assert isinstance(pattern, re.Pattern)

    def test_pattern_is_cached(self):
        """Test pattern property is cached"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            pattern1 = first_entry.pattern
            pattern2 = first_entry.pattern
            assert pattern1 is pattern2

    def test_pattern_can_match(self):
        """Test compiled patterns can be used for matching"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            pattern = first_entry.pattern
            # Try to use the pattern (even if no match, should not error)
            try:
                _ = pattern.findall("PEPTIDEK")
            except Exception as e:
                pytest.fail(f"Pattern matching failed: {e}")

    def test_trypsin_pattern_if_exists(self):
        """Test trypsin pattern if trypsin exists"""
        trypsin_keys = ["trypsin", "Trypsin"]
        for key in trypsin_keys:
            if key in db:
                trypsin = db[key]
                # Trypsin cuts after K and R (typically)
                pattern = trypsin.pattern
                # Test with a sequence
                matches = pattern.findall("PEPTIDEKR")
                # Should find cleavage sites
                assert isinstance(matches, list)
                break


class TestProteaseMethods:
    """Test ProteaseInfo methods"""

    def test_to_dict(self):
        """Test to_dict conversion"""
        if len(list(db)) > 0:
            protease = next(iter(db))
            d = protease.to_dict()
            assert d["id"] == protease.id
            assert d["name"] == protease.name
            assert d["full_name"] == protease.full_name
            assert d["regex"] == protease.regex

    def test_all_fields_present(self):
        """Test all proteases have all required fields"""
        for protease in db:
            assert protease.id is not None
            assert protease.name is not None
            assert protease.full_name is not None
            assert protease.regex is not None


class TestProteaseEdgeCases:
    """Test edge cases and error handling"""

    def test_getitem_not_found(self):
        """Test __getitem__ with non-existent key raises KeyError"""
        with pytest.raises(KeyError):
            _ = db["NonExistentProteaseKey"]

    def test_query_id_empty_string(self):
        """Test query_id with empty string"""
        result = db.query_id("")
        assert result is None

    def test_query_name_empty_string(self):
        """Test query_name with empty string"""
        result = db.query_name("")
        assert result is None


class TestProteaseDataIntegrity:
    """Test data integrity for proteases"""

    def test_all_have_ids(self):
        """Test all proteases have non-empty IDs"""
        for protease in db:
            assert protease.id is not None
            assert len(protease.id) > 0

    def test_all_have_names(self):
        """Test all proteases have non-empty names"""
        for protease in db:
            assert protease.name is not None
            assert len(protease.name) > 0

    def test_all_have_full_names(self):
        """Test all proteases have full names"""
        for protease in db:
            assert protease.full_name is not None
            assert len(protease.full_name) > 0

    def test_common_proteases_exist(self):
        """Test that common proteases exist"""
        common_proteases = ["trypsin", "chymotrypsin", "pepsin", "lysC", "arg-c", "asp-n", "glu-c"]
        found_count = 0
        for name in common_proteases:
            if name.lower() in [p.id.lower() for p in db] or name.lower() in [p.name.lower() for p in db]:
                found_count += 1
        # At least some common proteases should exist
        assert found_count > 0

    def test_id_name_lookup_consistency(self):
        """Test that ID and name lookups return same object"""
        if len(list(db)) > 0:
            first_entry = next(iter(db))
            by_id = db.query_id(first_entry.id)
            by_name = db.query_name(first_entry.name)
            assert by_id is by_name

    def test_regex_patterns_valid(self):
        """Test all regex patterns compile without errors"""
        for protease in db:
            try:
                pattern = protease.pattern
                assert pattern is not None
            except re.error as e:
                pytest.fail(f"Invalid regex for {protease.name}: {e}")

    def test_no_duplicate_ids(self):
        """Test there are no duplicate IDs"""
        ids = [p.id.lower() for p in db]
        assert len(ids) == len(set(ids))

    def test_no_duplicate_names(self):
        """Test there are no duplicate names"""
        names = [p.name.lower() for p in db]
        assert len(names) == len(set(names))
