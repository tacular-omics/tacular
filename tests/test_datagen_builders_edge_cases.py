"""Edge-case unit tests for the OBO builders, targeting defensive guards added during
code review (malformed xref/property_value lines, zero-count formula parts) that the
full-file reproduction tests in test_update.py don't happen to exercise.
"""

from io import StringIO

import pytest

from tacular._datagen import psimod, resid, unimod, xlmod
from tacular._datagen._utils import read_obo


def _terms(text):
    return read_obo(StringIO(text))


class TestUnimodEdgeCases:
    def test_malformed_xref_without_quoted_value_is_skipped(self):
        # A xref line with no '"..."' value must not raise (elems has < 2 parts).
        terms = _terms(
            '[Term]\nid: UNIMOD:1\nname: Test\nxref: delta_mono_mass_no_quotes\nxref: delta_mono_mass "1.0"\n'
        )
        infos = list(unimod._entries(terms))
        assert len(infos) == 1
        assert infos[0].monoisotopic_mass == 1.0

    def test_obsolete_term_skipped(self):
        terms = _terms("[Term]\nid: UNIMOD:1\nname: Test\nis_obsolete: true\n")
        assert list(unimod._entries(terms)) == []

    def test_root_node_skipped(self):
        terms = _terms("[Term]\nid: UNIMOD:0\nname: unimod root node\n")
        assert list(unimod._entries(terms)) == []

    def test_zero_count_formula_part_skipped(self):
        terms = _terms(
            "[Term]\nid: UNIMOD:1\nname: Test\n"
            'xref: delta_composition "C(0) H(2) O(1)"\n'
            'xref: delta_mono_mass "18.010565"\n'
        )
        infos = list(unimod._entries(terms))
        assert infos[0].dict_composition == {"H": 2, "O": 1}

    def test_entry_with_no_data_at_all_skipped(self):
        terms = _terms("[Term]\nid: UNIMOD:1\nname: Test\n")
        assert list(unimod._entries(terms)) == []


class TestPsimodEdgeCases:
    def test_malformed_xref_without_quoted_value_is_skipped(self):
        terms = _terms('[Term]\nid: MOD:00001\nname: Test\nxref: DiffMono_no_quotes\nxref: DiffMono "1.0"\n')
        infos = list(psimod._entries(terms))
        assert len(infos) == 1
        assert infos[0].monoisotopic_mass == 1.0

    def test_two_elements_with_no_count_between_them_implies_count_one(self):
        # DiffFormula "C H 2" -> "C" has no numeric token after it (next token is "H"),
        # so it's implicitly count=1, then "H 2" is a normal element/count pair.
        terms = _terms('[Term]\nid: MOD:00001\nname: Test\nxref: DiffFormula "C H 2"\nxref: DiffMono "14.01565"\n')
        infos = list(psimod._entries(terms))
        assert infos[0].formula == "CH2"
        assert infos[0].dict_composition == {"C": 1, "H": 2}

    def test_unparseable_generated_formula_falls_back_to_none(self, caplog):
        # A lowercase element symbol produces a formula string parse_formula_to_dict
        # rejects; the entry must fall back to None fields rather than raise.
        terms = _terms('[Term]\nid: MOD:00001\nname: Test\nxref: DiffFormula "n 2"\n')
        infos = list(psimod._entries(terms))
        assert infos[0].formula is None
        assert infos[0].dict_composition is None
        # The log must carry enough to diagnose the failure without a debugger: which
        # entry, the raw+generated input, the exception type/message, and a traceback.
        assert "Error parsing formula" in caplog.text
        assert "00001" in caplog.text
        assert "ValueError" in caplog.text
        assert "Unexpected character" in caplog.text
        assert "Traceback" in caplog.text


class TestResidEdgeCases:
    def test_term_without_definition_skipped(self):
        terms = _terms("[Term]\nid: MOD:1\nname: Test\n")
        assert list(resid._entries(terms)) == []

    def test_definition_without_resid_id_skipped(self):
        terms = _terms('[Term]\nid: MOD:1\nname: Test\ndef: "unrelated definition." []\n')
        assert list(resid._entries(terms)) == []

    def test_colon_fallback_xref_without_quotes_is_parsed(self):
        # xref lines without a quoted value (e.g. "DiffMono: 1.0") fall back to a
        # colon split rather than being dropped outright.
        terms = _terms('[Term]\nid: MOD:1\nname: Test\ndef: "x (RESID:AA0001)." []\nxref: DiffMono: 1.0\n')
        infos = list(resid._entries(terms))
        assert len(infos) == 1
        assert infos[0].id == "AA0001"
        assert infos[0].monoisotopic_mass == 1.0

    def test_duplicate_resid_id_across_terms_drops_both_at_build(self, tmp_path):
        obo = tmp_path / "PSI-MOD.obo"
        obo.write_text(
            "data-version: test\n\n"
            '[Term]\nid: MOD:1\nname: First\ndef: "x (RESID:AA0001)." []\nxref: DiffMono "1.0"\n\n'
            '[Term]\nid: MOD:2\nname: Second\ndef: "y (RESID:AA0001)." []\nxref: DiffMono "2.0"\n'
        )
        _version, infos = resid.build(obo)
        assert infos == []


class TestXlmodEdgeCases:
    def test_malformed_property_value_without_quoted_value_is_skipped(self):
        terms = _terms(
            "[Term]\nid: XLMOD:00001\nname: Test\n"
            "property_value: monoIsotopicMass_no_quotes\n"
            'property_value: monoIsotopicMass "1.0" xsd:double\n'
        )
        infos = list(xlmod._entries(terms))
        assert len(infos) == 1
        assert infos[0].monoisotopic_mass == 1.0

    def test_find_inherited_properties_unknown_parent_returns_none(self):
        lookup = xlmod._build_term_lookup(_terms("[Term]\nid: XLMOD:1\nname: Test\n"))
        assert xlmod._find_inherited_properties("XLMOD:99999", lookup) == (None, None, None)

    def test_find_inherited_properties_skips_malformed_property_value(self):
        terms = _terms("[Term]\nid: XLMOD:1\nname: Parent\nproperty_value: malformed_no_quotes\n")
        lookup = xlmod._build_term_lookup(terms)
        assert xlmod._find_inherited_properties("XLMOD:1", lookup) == (None, None, None)

    def test_one_level_inheritance_from_parent(self):
        terms = _terms(
            '[Term]\nid: XLMOD:2\nname: Parent\nproperty_value: bridgeFormula "C8" xsd:string\n\n'
            "[Term]\nid: XLMOD:1\nname: Test\nis_a: XLMOD:2 ! Parent\n"
        )
        infos = {i.id: i for i in xlmod._entries(terms)}
        assert infos["1"].formula == "C8"

    def test_two_level_inheritance_from_grandparent(self):
        terms = _terms(
            '[Term]\nid: XLMOD:3\nname: Grandparent\nproperty_value: bridgeFormula "C8" xsd:string\n\n'
            "[Term]\nid: XLMOD:2\nname: Parent\nis_a: XLMOD:3 ! Grandparent\n\n"
            "[Term]\nid: XLMOD:1\nname: Test\nis_a: XLMOD:2 ! Parent\n"
        )
        infos = {i.id: i for i in xlmod._entries(terms)}
        assert infos["1"].formula == "C8"

    def test_average_mass_property_key_detected_case_insensitively(self):
        terms = _terms(
            '[Term]\nid: XLMOD:1\nname: Test\nproperty_value: bridgeFormula "C8" xsd:string\n'
            'property_value: averageMass "100.5" xsd:double\n'
        )
        infos = list(xlmod._entries(terms))
        assert infos[0].average_mass == 100.5

    def test_double_space_produces_empty_token_that_is_skipped(self):
        terms = _terms('[Term]\nid: XLMOD:1\nname: Test\nproperty_value: bridgeFormula "C8  H12" xsd:string\n')
        infos = list(xlmod._entries(terms))
        assert infos[0].dict_composition == {"C": 8, "H": 12}

    def test_negative_isotope_count(self):
        terms = _terms('[Term]\nid: XLMOD:1\nname: Test\nproperty_value: bridgeFormula "-13C6" xsd:string\n')
        infos = list(xlmod._entries(terms))
        assert infos[0].dict_composition == {"13C": -6}

    def test_unrecognized_token_falls_back_to_none(self, caplog):
        terms = _terms('[Term]\nid: XLMOD:1\nname: Test\nproperty_value: bridgeFormula "abc" xsd:string\n')
        infos = list(xlmod._entries(terms))
        assert infos == []
        assert "Error parsing formula" in caplog.text
        assert "ValueError" in caplog.text
        assert "Unrecognized token" in caplog.text
        assert "Traceback" in caplog.text

    def test_non_numeric_mono_mass_logged_at_debug_and_falls_back(self, caplog):
        import logging

        terms = _terms(
            '[Term]\nid: XLMOD:1\nname: Test\nproperty_value: monoIsotopicMass "notanumber" xsd:double\n'
            'property_value: bridgeFormula "C8" xsd:string\n'
        )
        with caplog.at_level(logging.DEBUG):
            infos = list(xlmod._entries(terms))
        assert infos[0].monoisotopic_mass == pytest.approx(96.0)
        assert "Could not parse monoIsotopicMass" in caplog.text
        assert "ValueError" in caplog.text

    def test_non_numeric_mono_mass_falls_back_to_calculated(self):
        terms = _terms(
            '[Term]\nid: XLMOD:1\nname: Test\nproperty_value: monoIsotopicMass "notanumber" xsd:double\n'
            'property_value: bridgeFormula "C8" xsd:string\n'
        )
        infos = list(xlmod._entries(terms))
        assert infos[0].monoisotopic_mass == pytest.approx(96.0)

    def test_non_numeric_avg_mass_falls_back_to_calculated(self):
        terms = _terms(
            '[Term]\nid: XLMOD:1\nname: Test\nproperty_value: bridgeFormula "C8" xsd:string\n'
            'property_value: averageMass "notanumber" xsd:double\n'
        )
        infos = list(xlmod._entries(terms))
        assert infos[0].average_mass == pytest.approx(96.086, abs=1e-2)
