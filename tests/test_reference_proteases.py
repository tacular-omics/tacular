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
"""

import re
from collections.abc import Callable
from itertools import product

import pytest

from tacular.proteases.data import PROTEASES_DICT, Proteases

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"
PAIRS = ["".join(p) for p in product(AMINO_ACIDS, repeat=2)]

# (P1, P1') -> cleaves?
PEPTIDECUTTER: dict[Proteases, Callable[[str, str], bool]] = {
    Proteases.ARG_C: lambda p1, p1p: p1 == "R",
    Proteases.ASP_N: lambda p1, p1p: p1p == "D",
    Proteases.GLU_C: lambda p1, p1p: p1 == "E",  # "Glutamyl endopeptidase"
    Proteases.LYS_C: lambda p1, p1p: p1 == "K",
    Proteases.LYS_N: lambda p1, p1p: p1p == "K",
    Proteases.PROTEINASE_K: lambda p1, p1p: p1 in "AEFILTVWY",
    Proteases.TRYPSIN: lambda p1, p1p: p1 in "KR" and p1p != "P",
    Proteases.THERMOLYSIN: lambda p1, p1p: p1 not in "DE" and p1p in "AFILMV",
}


def _cleaves_between(regex: str, pair: str) -> bool:
    return any(m.end() == 1 for m in re.finditer(regex, pair))


@pytest.mark.parametrize("protease", list(PEPTIDECUTTER), ids=str)
def test_regex_matches_peptidecutter_rule(protease):
    regex = PROTEASES_DICT[protease].regex
    rule = PEPTIDECUTTER[protease]
    wrong = [pair for pair in PAIRS if _cleaves_between(regex, pair) != rule(pair[0], pair[1])]
    assert not wrong, f"{protease}: {len(wrong)} P1-P1' pairs disagree, e.g. {wrong[:10]}"


def test_thermolysin_cleaves_n_terminal_to_hydrophobic_residues():
    # PeptideCutter: P1' in A, F, I, L, M, V; P1 not D or E.
    regex = PROTEASES_DICT[Proteases.THERMOLYSIN].regex
    assert re.split(regex, "GGLGGEVGG") == ["GG", "LGGEVGG"]
