"""Invariants checked over every entry of tacular's small hand-curated tables.

Each test loops over the whole table and reports every failing entry in one message.
The ontology tables (UNIMOD, PSI-MOD, ...) are covered by ``test_reference_data.py`` and
``test_properties.py``; the isobaric-tag and SILAC monoisotopic masses by ``test_labels.py``.
"""

from collections import defaultdict

import pytest

from tacular import (
    AA_LOOKUP,
    ELEMENT_LOOKUP,
    FRAGMENT_ION_LOOKUP,
    ISOBARIC_TAG_LOOKUP,
    MONOSACCHARIDE_LOOKUP,
    NEUTRAL_DELTA_LOOKUP,
    PROTEASE_LOOKUP,
    REFMOL_LOOKUP,
    SILAC_LOOKUP,
)

MASS_TOL = 1e-6

COMPOSITION_TABLES = {
    "amino acid": AA_LOOKUP,
    "fragment ion": FRAGMENT_ION_LOOKUP,
    "neutral delta": NEUTRAL_DELTA_LOOKUP,
    "reference molecule": REFMOL_LOOKUP,
    "monosaccharide": MONOSACCHARIDE_LOOKUP,
    "isobaric tag": ISOBARIC_TAG_LOOKUP,
    "SILAC label": SILAC_LOOKUP,
}


def _element_mass(composition, monoisotopic):
    return sum(ELEMENT_LOOKUP.get_mass(symbol, monoisotopic=monoisotopic) * n for symbol, n in composition.items())


def test_stored_masses_match_the_element_table():
    """Catches a mistyped or stale stored mass: after an element-table refresh or a hand
    edit, a generated mass that no longer equals the mass of the entry's own composition.
    Covers the average masses too, which no reference fixture checks."""
    wrong = []
    for table, lookup in COMPOSITION_TABLES.items():
        for info in lookup.values():
            composition = info.dict_composition
            for monoisotopic, stored in ((True, info.monoisotopic_mass), (False, info.average_mass)):
                if not composition:
                    # placeholders (B, Z, the generic da/wa ions) carry no mass; X carries 0.0
                    if stored not in (None, 0.0):
                        wrong.append(f"{table} {info.name!r}: mass {stored} without a composition")
                    continue
                expected = _element_mass(composition, monoisotopic)
                if stored is None or abs(stored - expected) > MASS_TOL:
                    kind = "mono" if monoisotopic else "avg"
                    wrong.append(f"{table} {info.name!r}: {kind} {stored} != {expected:.7f} from {dict(composition)}")
    assert not wrong, f"{len(wrong)} stored masses disagree with the element table:\n" + "\n".join(wrong)


def _key_fields():
    """(table, lookup, query function, key of each entry) for every key a table is indexed by."""
    yield "amino acid one-letter", AA_LOOKUP, AA_LOOKUP.query_one_letter, lambda i: i.id
    yield "amino acid three-letter", AA_LOOKUP, AA_LOOKUP.query_three_letter, lambda i: i.three_letter_code
    yield "amino acid name", AA_LOOKUP, AA_LOOKUP.query_name, lambda i: i.name
    yield "fragment ion id", FRAGMENT_ION_LOOKUP, FRAGMENT_ION_LOOKUP.query_id, lambda i: i.id
    yield "fragment ion name", FRAGMENT_ION_LOOKUP, FRAGMENT_ION_LOOKUP.query_name, lambda i: i.name
    yield "neutral delta formula", NEUTRAL_DELTA_LOOKUP, NEUTRAL_DELTA_LOOKUP.query_formula, lambda i: i.formula
    yield "neutral delta name", NEUTRAL_DELTA_LOOKUP, NEUTRAL_DELTA_LOOKUP.query_name, lambda i: i.name
    yield "reference molecule name", REFMOL_LOOKUP, REFMOL_LOOKUP.query_name, lambda i: i.name
    yield "monosaccharide name", MONOSACCHARIDE_LOOKUP, MONOSACCHARIDE_LOOKUP.query_name, lambda i: i.name
    yield "protease id", PROTEASE_LOOKUP, PROTEASE_LOOKUP.query_id, lambda i: i.id
    yield "protease name", PROTEASE_LOOKUP, PROTEASE_LOOKUP.query_name, lambda i: i.name
    for table, lookup in (("isobaric tag", ISOBARIC_TAG_LOOKUP), ("SILAC label", SILAC_LOOKUP)):
        yield f"{table} name", lookup, lookup.query_name, lambda i: i.name
        yield f"{table} alias", lookup, lookup.query_name, lambda i: i.aliases


def test_every_key_returns_its_own_entry():
    """Catches a broken index and two entries sharing a key (case-insensitively), where the
    later entry silently shadows the earlier one: every entry must come back from its own
    query method and from ``lookup[key]``, in any case."""
    wrong = []
    for field, lookup, query, get_keys in _key_fields():
        owners = defaultdict(list)
        for info in lookup.values():
            keys = get_keys(info)
            for key in (keys,) if isinstance(keys, str) else keys:
                owners[str(key).lower()].append(info)
                for variant in {str(key), str(key).lower(), str(key).upper()}:
                    if query(variant) is not info or lookup[variant] is not info:
                        wrong.append(f"{field} {variant!r} does not return {info!r}")
        shared = {key: [i.name for i in infos] for key, infos in owners.items() if len(infos) > 1}
        if shared:
            wrong.append(f"{field}: keys shared by several entries: {shared}")
    assert not wrong, f"{len(wrong)} lookup keys are broken:\n" + "\n".join(wrong)


def test_monoisotopic_flag_marks_the_element_default_isotope():
    """Catches an ``is_monoisotopic`` flag on the wrong isotope after a NIST refresh: each
    element has exactly one flagged isotope, it is the most abundant one when the element
    has natural abundances, and its mass is the element's monoisotopic mass. Also catches
    an isotope filed under the wrong atomic number."""
    isotopes = defaultdict(list)
    for (symbol, mass_number), info in ELEMENT_LOOKUP.items():
        if mass_number is not None:
            isotopes[str(symbol)].append(info)
    wrong = []
    for symbol, infos in isotopes.items():
        element = ELEMENT_LOOKUP[symbol]
        flagged = [i.mass_number for i in infos if i.is_monoisotopic]
        if len(flagged) != 1:
            wrong.append(f"{symbol}: flagged isotopes {flagged}")
            continue
        mono = ELEMENT_LOOKUP[(symbol, flagged[0])]
        if mono.mass != element.mass:
            wrong.append(f"{symbol}: flagged {flagged[0]}{symbol} mass {mono.mass} != element mass {element.mass}")
        if any(i.abundance for i in infos):
            top = max(infos, key=lambda i: i.abundance or 0.0)
            if top is not mono:
                wrong.append(f"{symbol}: flagged {flagged[0]}{symbol} but {top.mass_number}{symbol} is most abundant")
        stray = [i.mass_number for i in infos if i.number != element.number]
        if stray:
            wrong.append(f"{symbol}: isotopes {stray} have an atomic number other than {element.number}")
    assert not wrong, f"{len(wrong)} elements have a bad monoisotopic flag:\n" + "\n".join(wrong)


if __name__ == "__main__":
    pytest.main([__file__])
