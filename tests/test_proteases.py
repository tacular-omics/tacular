import re

import pytest

import tacular as t
from tacular import PROTEASE_LOOKUP as db


@pytest.fixture
def first_protease():
    """Fixture to provide the first protease from the database"""
    proteases = list(db)
    if not proteases:
        pytest.skip("No proteases in database")
    return proteases[0]


class TestProteaseLookupBasics:
    """Test basic protease lookup operations"""

    def test_getitem_by_id(self, first_protease):
        """Test __getitem__ with protease IDs"""
        result = db[first_protease.id]
        assert result.id.lower() == first_protease.id.lower()
        assert result.name is not None

    def test_getitem_by_name(self, first_protease):
        """Test __getitem__ with protease names"""
        result = db[first_protease.name]
        assert result.name.lower() == first_protease.name.lower()

    def test_contains(self, first_protease):
        """Test __contains__ operator"""
        assert first_protease.id in db
        assert first_protease.name in db
        assert "NotAProtease" not in db

    def test_iter(self):
        """Test iteration over proteases"""
        proteases: list[t.ProteaseInfo] = list(db)
        assert len(proteases) > 0
        # All should have IDs and names
        for protease in proteases:
            assert protease.id is not None
            assert protease.name is not None

    def test_get_with_default(self):
        """Test get() method with default value"""
        result = db.get("NonexistentProtease")
        assert result is None

    def test_case_insensitivity(self, first_protease):
        """Test case-insensitive lookups"""
        lower = db.query_id(first_protease.id.lower())
        upper = db.query_id(first_protease.id.upper())
        assert lower is upper


class TestProteaseLookupQueryMethods:
    """Test protease query methods"""

    def test_query_id(self, first_protease):
        """Test query_id method"""
        result = db.query_id(first_protease.id)
        assert result is not None
        assert result.id.lower() == first_protease.id.lower()

    def test_query_id_not_found(self):
        """Test query_id with non-existent ID"""
        result = db.query_id("nonexistentprotease")
        assert result is None

    def test_query_name(self, first_protease):
        """Test query_name method"""
        result = db.query_name(first_protease.name)
        assert result is not None
        assert result.name.lower() == first_protease.name.lower()

    def test_query_name_not_found(self):
        """Test query_name with non-existent name"""
        result = db.query_name("NonExistentProteaseName")
        assert result is None

    def test_query_name_case_insensitive(self, first_protease):
        """Test query_name is case insensitive"""
        lower = db.query_name(first_protease.name.lower())
        upper = db.query_name(first_protease.name.upper())
        assert lower is upper


class TestProteaseRegexPatterns:
    """Test protease regex patterns and compilation"""

    def test_all_have_regex(self):
        """Test all proteases have regex patterns"""
        for protease in db:
            assert protease.regex is not None
            assert len(protease.regex) > 0

    def test_pattern_compilation(self, first_protease):
        """Test pattern cached property compiles regex"""
        pattern = first_protease.pattern
        assert pattern is not None
        assert isinstance(pattern, re.Pattern)

    def test_pattern_is_cached(self, first_protease):
        """Test pattern property is cached"""
        pattern1 = first_protease.pattern
        pattern2 = first_protease.pattern
        assert pattern1 is pattern2

    def test_pattern_can_match(self, first_protease):
        """Test compiled patterns can be used for matching"""
        pattern = first_protease.pattern
        # Try to use the pattern (even if no match, should not error)
        try:
            _ = pattern.findall("PEPTIDEK")
        except Exception as e:
            pytest.fail(f"Pattern matching failed: {e}")

    def test_trypsin_pattern_if_exists(self):
        """Test trypsin pattern if trypsin exists"""
        trypsin_keys = ["trypsin", "TryPsiN"]
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

    def test_to_dict(self, first_protease):
        """Test to_dict conversion"""
        d = first_protease.to_dict()
        assert d["id"] == first_protease.id
        assert d["name"] == first_protease.name
        assert d["full_name"] == first_protease.full_name
        assert d["regex"] == first_protease.regex

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

    @pytest.mark.parametrize("attr", ["id", "name", "full_name"])
    def test_all_have_required_fields(self, attr):
        """Test all proteases have required fields populated"""
        for protease in db:
            value = getattr(protease, attr)
            assert value is not None
            assert len(value) > 0

    def test_common_proteases_exist(self):
        """Test that common proteases exist"""
        common_proteases = ["trypsin", "chymotrypsin", "pepsin", "lysC", "arg-c", "asp-n", "glu-c"]
        found_count = 0
        for name in common_proteases:
            if name.lower() in [p.id.lower() for p in db] or name.lower() in [p.name.lower() for p in db]:
                found_count += 1
        # At least some common proteases should exist
        assert found_count > 0

    def test_id_name_lookup_consistency(self, first_protease):
        """Test that ID and name lookups return same object"""
        by_id = db.query_id(first_protease.id)
        by_name = db.query_name(first_protease.name)
        assert by_id is by_name

    def test_regex_patterns_valid(self):
        """Test all regex patterns compile without errors"""
        for protease in db:
            try:
                pattern = protease.pattern
                assert pattern is not None
            except re.error as e:
                pytest.fail(f"Invalid regex for {protease.name}: {e}")

    @pytest.mark.parametrize("attr", ["id", "name"])
    def test_no_duplicate_fields(self, attr):
        """Test there are no duplicate values for specific fields"""
        values = [getattr(p, attr).lower() for p in db]
        assert len(values) == len(set(values))


if __name__ == "__main__":
    pytest.main([__file__])
