"""Unit tests for tacular._datagen._utils, the shared OBO/formula parsing helpers."""

from io import StringIO

import pytest

from tacular._datagen._utils import (
    calculate_mass,
    format_composition_string,
    get_id_and_name,
    get_obo_metadata,
    is_obsolete,
    parse_formula_to_dict,
    read_obo,
)


class TestCalculateMass:
    def test_monoisotopic(self):
        assert calculate_mass({"C": 2, "H": 2, "O": 1}) == pytest.approx(42.010565, abs=1e-5)

    def test_average(self):
        assert calculate_mass({"C": 1}, monoisotopic=False) == pytest.approx(12.0107, abs=1e-3)

    def test_isotope_key(self):
        assert calculate_mass({"13C": 1}) == pytest.approx(13.003355, abs=1e-5)


class TestFormatCompositionString:
    def test_empty_composition(self):
        assert format_composition_string({}) == ""

    def test_hill_order_c_then_h_then_alphabetical(self):
        assert format_composition_string({"O": 1, "N": 1, "C": 2, "H": 3}) == "C2H3NO"

    def test_count_of_one_omitted(self):
        assert format_composition_string({"C": 1}) == "C"


class TestGetOboMetadata:
    def test_extracts_header_before_first_term(self):
        f = StringIO("format-version: 1.4\ndata-version: 2026\n\n[Term]\nid: X:1\n")
        meta = get_obo_metadata(f)
        assert meta == {"format-version": "1.4", "data-version": "2026"}

    def test_skips_header_lines_without_colon_space(self):
        # A header line lacking ": " must be skipped, not raise.
        f = StringIO("format-version: 1.4\nnocolonhere\ndata-version: 2026\n\n[Term]\n")
        meta = get_obo_metadata(f)
        assert meta == {"format-version": "1.4", "data-version": "2026"}


class TestReadObo:
    def test_parses_single_term(self):
        f = StringIO('[Term]\nid: X:1\nname: Foo\nxref: a "1"\n')
        terms = read_obo(f)
        assert len(terms) == 1
        assert terms[0]["id"] == ["X:1"]
        assert terms[0]["name"] == ["Foo"]

    def test_skips_typedef_stanzas(self):
        f = StringIO("[Typedef]\nid: is_a\n\n[Term]\nid: X:1\nname: Foo\n")
        terms = read_obo(f)
        assert len(terms) == 1
        assert terms[0]["id"] == ["X:1"]

    def test_repeated_tag_accumulates_list(self):
        f = StringIO('[Term]\nid: X:1\nname: Foo\nxref: a "1"\nxref: b "2"\n')
        terms = read_obo(f)
        assert terms[0]["xref"] == ['a "1"', 'b "2"']

    def test_line_without_colon_space_is_skipped(self):
        f = StringIO("[Term]\nid: X:1\nname: Foo\nnocolonspace\n")
        terms = read_obo(f)
        assert terms[0]["id"] == ["X:1"]
        assert "nocolonspace" not in terms[0]

    def test_header_line_without_colon_space_is_skipped(self):
        # Header region (before first [Term]) with a malformed line must not raise.
        f = StringIO("garbage-no-colon\nformat-version: 1.4\n\n[Term]\nid: X:1\nname: Foo\n")
        terms = read_obo(f)
        assert len(terms) == 1


class TestGetIdAndName:
    def test_normal_term(self):
        assert get_id_and_name({"id": ["X:1"], "name": ["Foo"]}) == ("X:1", "Foo")

    def test_missing_id_raises(self):
        with pytest.raises(ValueError, match="Entry id is None"):
            get_id_and_name({"id": [], "name": ["Foo"]})

    def test_missing_name_raises(self):
        with pytest.raises(ValueError, match="Entry name is None"):
            get_id_and_name({"id": ["X:1"], "name": []})


class TestIsObsolete:
    def test_default_false(self):
        assert is_obsolete({}) is False

    def test_true(self):
        assert is_obsolete({"is_obsolete": ["true"]}) is True

    def test_case_insensitive_true(self):
        assert is_obsolete({"is_obsolete": ["True"]}) is True

    def test_unexpected_value_is_lenient_not_obsolete(self):
        # A future OBO release with an unexpected value must not crash an update.
        assert is_obsolete({"is_obsolete": ["maybe"]}) is False


class TestParseFormulaToDict:
    def test_empty_string(self):
        assert parse_formula_to_dict("") == {}

    def test_none(self):
        assert parse_formula_to_dict(None) == {}

    def test_simple_formula(self):
        assert parse_formula_to_dict("C2H6O") == {"C": 2, "H": 6, "O": 1}

    def test_negative_count(self):
        assert parse_formula_to_dict("C-1H2") == {"C": -1, "H": 2}

    def test_isotope_bracket_with_count(self):
        assert parse_formula_to_dict("[13C2]H6") == {"13C": 2, "H": 6}

    def test_isotope_bracket_without_count_defaults_to_one(self):
        assert parse_formula_to_dict("[13C]") == {"13C": 1}

    def test_isotope_bracket_negative_count(self):
        assert parse_formula_to_dict("[13C-1]") == {"13C": -1}

    def test_mixed_isotope_and_plain(self):
        assert parse_formula_to_dict("C2[13C6]H5") == {"C": 2, "13C": 6, "H": 5}

    def test_whitespace_is_skipped(self):
        assert parse_formula_to_dict("C2 H6 O") == {"C": 2, "H": 6, "O": 1}

    def test_unclosed_bracket_raises(self):
        with pytest.raises(ValueError, match="Unclosed bracket"):
            parse_formula_to_dict("[13C2")

    def test_invalid_isotope_content_raises(self):
        with pytest.raises(ValueError, match="Invalid isotope format"):
            parse_formula_to_dict("[notanisotope]")

    def test_unexpected_character_raises(self):
        with pytest.raises(ValueError, match="Unexpected character"):
            parse_formula_to_dict("c2")  # lowercase leading char is not a valid element start
