"""Thermolysin's cleavage sites checked against pyteomics on real UniProt sequences.

The fixture ``tests/reference/data/thermolysin_cleavage_sites.json`` holds two sequences
downloaded from UniProtKB on 2026-11-20
(``https://rest.uniprot.org/uniprotkb/P02769.fasta`` and ``.../P00698.fasta``) and the
cleavage positions produced by **pyteomics 5.0.2**, whose
``pyteomics.parser.expasy_rules["thermolysin"]`` is ``'[^DE](?=[AFILMV][^P])'``. Neither
the sequences nor the expected positions come from tacular, before or after this change.

The rule tacular ships is the PSI-MS controlled vocabulary term MS:1003978,
``name: (?<=[^DE])(?=[AFILMV][^P])``, ``def: "Regular expression for Thermolysin."``
(psi-ms.obo, HUPO-PSI/psi-ms-CV master, read 2026-11-20), which encodes ExPASy
PeptideCutter's sentence "Pro blocks when located in position P2' but not when found in
position P1."
"""

import json
from pathlib import Path

import pytest

from tacular import PROTEASE_LOOKUP

FIXTURE = json.loads((Path(__file__).parent / "reference" / "data" / "thermolysin_cleavage_sites.json").read_text())
ENTRIES = FIXTURE["entries"]


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["accession"] for e in ENTRIES])
def test_sites_match_pyteomics_on_a_real_sequence(entry):
    """OUTSIDE EXPECTATION: positions computed by pyteomics, not by tacular."""
    pattern = PROTEASE_LOOKUP["Thermolysin"].pattern
    sites = sorted({m.start() for m in pattern.finditer(entry["sequence"])})
    assert sites == entry["cleavage_sites"]


def test_proline_in_p2_prime_blocks_cleavage():
    """ExPASy: "Pro blocks when located in position P2' but not when found in position P1."

    ``CF|LP`` is position 11 of P00698, which pyteomics does not cut and the old rule did.
    """
    pattern = PROTEASE_LOOKUP["Thermolysin"].pattern
    # The site under test is the one before the L, i.e. index 2; "CFLP" keeps its site at
    # index 1 (before the F), which neither rule disputes.
    assert 2 not in {m.start() for m in pattern.finditer("CFLP")}
    assert 2 in {m.start() for m in pattern.finditer("CFLA")}
    # P1 proline does not block: the residue before the site may be P.
    assert 2 in {m.start() for m in pattern.finditer("CPLA")}


def test_no_site_before_the_first_or_last_residue():
    """MS:1003978 requires a residue before the site and a non-proline residue after P1'."""
    pattern = PROTEASE_LOOKUP["Thermolysin"].pattern
    assert [m.start() for m in pattern.finditer("AAAA")] == [1, 2]
