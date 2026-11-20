"""Protease regexes checked against the ExPASy PeptideCutter cleavage rules.

Source: https://web.expasy.org/peptide_cutter/peptidecutter_enzymes.html ("Cleavage
rules" table, after Keil 1992), retrieved 2026-09-23. Each rule below is written from
that table as a predicate on the residues either side of a bond (P1 | P1'), and every
one of the 400 P1-P1' pairs of the standard amino acids is checked.

Known differences, not modelled by tacular's single-regex rules:

- Trypsin: PeptideCutter's P2-dependent exceptions (WKP and MRP still cleave; CKD, DKD,
  CKH, CKY, CRK, RRH, RRR do not) are ignored.
- ``chymotrypsin`` / ``chymotrypsin_low`` follow the common search-engine convention
  (C-term to F, W, Y, L; high adds "not before P"), not PeptideCutter's high (F, Y, W)
  and low (F, Y, W, M, L, H with P1' exceptions) sets.
- Pepsin: PeptideCutter cleaves on either side of F, L, W, Y with P3/P2/P2' exceptions;
  tacular cleaves only C-terminal to them.
- Proalanase, pancreatic elastase and the Promega chymotrypsin variants have no
  PeptideCutter entry.
- Thermolysin is not in the P1-P1' table below: its rule depends on P2' ("Pro blocks when
  located in position P2'", the same page's text, which its own table omits), so a
  two-residue window cannot express it. It is checked in
  ``tests/test_reference_thermolysin.py`` against pyteomics on real sequences instead.
"""

import re
from collections.abc import Callable
from itertools import product

import pytest

from tacular.proteases.data import PROTEASE_DICT, Protease

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
PAIRS = ["".join(p) for p in product(AMINO_ACIDS, repeat=2)]

# (P1, P1') -> cleaves?
PEPTIDECUTTER: dict[Protease, Callable[[str, str], bool]] = {
    Protease.ARG_C: lambda p1, p1p: p1 == "R",
    Protease.ASP_N: lambda p1, p1p: p1p == "D",
    Protease.GLU_C: lambda p1, p1p: p1 == "E",  # "Glutamyl endopeptidase"
    Protease.LYS_C: lambda p1, p1p: p1 == "K",
    Protease.LYS_N: lambda p1, p1p: p1p == "K",
    Protease.PROTEINASE_K: lambda p1, p1p: p1 in "AEFILTVWY",
    Protease.TRYPSIN: lambda p1, p1p: p1 in "KR" and p1p != "P",
}


def _cleaves_between(regex: str, pair: str) -> bool:
    return any(m.end() == 1 for m in re.finditer(regex, pair))


@pytest.mark.parametrize("protease", list(PEPTIDECUTTER), ids=str)
def test_regex_matches_peptidecutter_rule(protease):
    regex = PROTEASE_DICT[protease].regex
    rule = PEPTIDECUTTER[protease]
    wrong = [pair for pair in PAIRS if _cleaves_between(regex, pair) != rule(pair[0], pair[1])]
    assert not wrong, f"{protease}: {len(wrong)} P1-P1' pairs disagree, e.g. {wrong[:10]}"


def test_thermolysin_cleaves_n_terminal_to_hydrophobic_residues():
    # PeptideCutter: P1' in A, F, I, L, M, V; P1 not D or E. The P2' half of the rule is
    # covered in tests/test_reference_thermolysin.py.
    regex = PROTEASE_DICT[Protease.THERMOLYSIN].regex
    assert re.split(regex, "GGLGGEVGG") == ["GG", "LGGEVGG"]
