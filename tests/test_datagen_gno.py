"""Unit tests for tacular._datagen.gno using small synthetic OBO fixtures.

The real GNOme.obo is ~129 MB, too slow for the unit suite (see test_update.py,
which skips it and instead reproduces the bundled JSON in an integration test).
These tests exercise the parsing logic directly against minimal snippets.
"""

from tacular._datagen import gno
from tacular._datagen._utils import get_obo_metadata, read_obo

HEADER = "format-version: 1.2\ndata-version: 2025-10-10\n\n"


def _terms(text):
    from io import StringIO

    f = StringIO(HEADER + text)
    version = get_obo_metadata(f).get("data-version", "unknown")
    return version, read_obo(f)


def test_build_parses_valid_composition(tmp_path):
    obo = tmp_path / "GNOme.obo"
    obo.write_text(
        HEADER
        + "[Term]\n"
        + "id: GNO:00000001\n"
        + "name: glycan one\n"
        + 'property_value: GNO:00000202 "Hex(6)dHex(1)" xsd:string\n'
    )
    version, infos = gno.build(obo)
    assert version == "2025-10-10"
    assert len(infos) == 1
    info = infos[0]
    assert info.id == "00000001"
    assert info.formula == "C42H70O34"
    assert info.dict_composition == {"C": 42, "H": 70, "O": 34}
    assert info.monoisotopic_mass is not None
    assert info.average_mass is not None


def test_unknown_glycan_symbol_skips_entry(caplog):
    _, terms = _terms(
        '[Term]\nid: GNO:00000002\nname: bad glycan\nproperty_value: GNO:00000202 "Xenon(1)" xsd:string\n'
    )
    infos = list(gno._entries(terms))
    assert infos == []
    # The warning must name the offending symbol, the full composition string it came
    # from, and the known-good symbols, so the cause is clear without re-deriving it.
    assert "Xenon" in caplog.text
    assert "Xenon(1)" in caplog.text
    assert "Hex" in caplog.text


def test_obsolete_entry_skipped():
    _, terms = _terms(
        "[Term]\nid: GNO:00000003\nname: obsolete glycan\nis_obsolete: true\n"
        'property_value: GNO:00000202 "Hex(1)" xsd:string\n'
    )
    infos = list(gno._entries(terms))
    assert infos == []


def test_entry_without_composition_property_skipped():
    _, terms = _terms(
        '[Term]\nid: GNO:00000004\nname: no composition\nproperty_value: GNO:00000022 "G00000ZZ" xsd:string\n'
    )
    infos = list(gno._entries(terms))
    assert infos == []


def test_malformed_property_value_line_ignored():
    # A property_value line with no quoted value (no '"') must not raise.
    _, terms = _terms("[Term]\nid: GNO:00000005\nname: malformed\nproperty_value: GNO:00000202 unquoted_value\n")
    infos = list(gno._entries(terms))
    assert infos == []


def test_multi_symbol_composition_accumulates():
    comp = gno._parse_glycan_composition("Hex(2)HexNAc(1)Fuc(1)")
    assert comp == {"C": 6 * 2 + 8 + 6, "H": 10 * 2 + 13 + 10, "N": 1, "O": 5 * 2 + 5 + 4}


def test_composition_to_formula_orders_c_h_n_o_then_alphabetical():
    from collections import Counter

    comp = Counter({"S": 1, "C": 2, "O": 3, "H": 4})
    assert gno._composition_to_formula(comp) == "C2H4O3S"
