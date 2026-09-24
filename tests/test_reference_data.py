"""Bundled data checked against frozen upstream reference values.

The fixtures in ``tests/reference/data/`` were produced by
``tests/reference/generate_reference.py`` (sources and versions in its docstring) with
parsing code independent of tacular. Tolerance is 1e-6 Da unless a test says otherwise.
Reads the bundled ``data.py`` modules directly, so a refreshed user cache cannot mask a
bad snapshot.
"""

import json
from pathlib import Path

import pytest

from tacular.amino_acids.data import AMINO_ACID_INFOS
from tacular.elements import ELEMENT_LOOKUP
from tacular.gno.data import GNO_GLYCANS
from tacular.psimod.data import PSI_MODIFICATIONS
from tacular.resid.data import RESID_MODIFICATIONS
from tacular.unimod.data import UNIMOD_MODIFICATIONS
from tacular.uniprot_ptm.data import UNIPROT_PTM_MODIFICATIONS
from tacular.xlmod.data import XLMOD_MODIFICATIONS

REF = Path(__file__).parent / "reference" / "data"
TOL = 1e-6

_nist = json.loads((REF / "nist_isotopes.json").read_text())
NIST = [dict(zip(_nist["columns"], row, strict=True)) for row in _nist["rows"]]
ONTOLOGY = json.loads((REF / "ontology_masses.json").read_text())
AMINO_ACIDS = json.loads((REF / "amino_acids.json").read_text())

BUNDLED = {
    "unimod": UNIMOD_MODIFICATIONS,
    "psimod": PSI_MODIFICATIONS,
    "resid": RESID_MODIFICATIONS,
    "xlmod": XLMOD_MODIFICATIONS,
    "uniprot_ptm": UNIPROT_PTM_MODIFICATIONS,
    "gno": GNO_GLYCANS,
}


def _mass(composition, monoisotopic=True):
    total = 0.0
    for symbol, count in composition.items():
        info = ELEMENT_LOOKUP[symbol]
        total += (info.mass if monoisotopic else info.average_mass) * count
    return total


# --- elements -------------------------------------------------------------------------


def test_every_nist_isotope_matches():
    wrong = []
    for iso in NIST:
        info = ELEMENT_LOOKUP[(iso["symbol"], iso["a"])]
        if (
            abs(info.mass - iso["mass"]) > TOL
            or abs((info.abundance or 0.0) - iso["abundance"]) > 1e-9
            or info.number != iso["z"]
        ):
            wrong.append((iso, info))
    assert not wrong, f"{len(wrong)} isotopes differ from NIST, e.g. {wrong[:3]}"


def test_no_isotopes_beyond_nist():
    nist_keys = {(i["symbol"], i["a"]) for i in NIST}
    extra = [(i.symbol, i.mass_number) for i in ELEMENT_LOOKUP.values() if i.mass_number is not None]
    assert set(extra) <= nist_keys


def test_monoisotopic_is_most_abundant_isotope():
    by_element: dict[str, list[dict]] = {}
    for iso in NIST:
        by_element.setdefault(iso["symbol"], []).append(iso)
    for symbol, isos in by_element.items():
        if not any(i["abundance"] for i in isos):
            continue
        top = max(isos, key=lambda i: i["abundance"])
        assert ELEMENT_LOOKUP[symbol].mass == pytest.approx(top["mass"], abs=TOL), symbol


def test_average_mass_is_abundance_weighted():
    # Convention: the average mass is the abundance-weighted mean of the NIST isotopic
    # composition, not the IUPAC standard atomic weight. The two differ in the third or
    # fourth decimal for some elements (Se 78.959 vs 78.971, Hg 200.599 vs 200.592).
    by_element: dict[str, list[dict]] = {}
    for iso in NIST:
        by_element.setdefault(iso["symbol"], []).append(iso)
    for symbol, isos in by_element.items():
        if not any(i["abundance"] for i in isos):
            continue
        expected = sum(i["mass"] * i["abundance"] for i in isos)
        assert ELEMENT_LOOKUP[symbol].average_mass == pytest.approx(expected, abs=TOL), symbol


# --- ontology stated masses -------------------------------------------------------------


@pytest.mark.parametrize("source", list(BUNDLED))
def test_ontology_masses_match_upstream(source):
    """Stated upstream masses (UNIMOD delta_mono/avge_mass, PSI-MOD DiffMono/DiffAvg,
    XLMOD monoIsotopicMass, UniProt MM/MA) and GNOme composition masses."""
    bundled = BUNDLED[source]
    missing, wrong = [], []
    for key, (mono, avg) in ONTOLOGY[source].items():
        info = bundled.get(key)
        if info is None:
            missing.append(key)
            continue
        for want, got in ((mono, info.monoisotopic_mass), (avg, info.average_mass)):
            if want is not None and (got is None or abs(got - want) > TOL):
                wrong.append((key, info.name, got, want))
    assert not missing, f"{len(missing)} {source} entries missing, e.g. {missing[:5]}"
    assert not wrong, f"{len(wrong)} {source} masses differ from upstream, e.g. {wrong[:5]}"


# Entries whose upstream stated mass disagrees with their own upstream composition; tacular
# keeps the stated mass, as the upstream does. Checked on 2026-09-23 against the same files;
# reasons are the likeliest cause of each difference, not confirmed by the upstream.
KNOWN_UPSTREAM_MISMATCHES: dict[str, dict[str, str]] = {
    "unimod": {
        "291": "stated mass uses an older Hg-202 isotope mass (-2.6e-5 Da)",
    },
    "psimod": {
        "02105": "DiffMono is O2 (+31.9898) but DiffFormula is O",
    },
    "resid": {},
    "xlmod": {
        "01024": "stated mass is one H (or H+) above the formula",
        "01025": "stated mass is one electron mass below the formula",
        "01026": "stated mass is one H (or H+) above the formula",
        "01027": "stated mass is one electron mass below the formula",
        "01028": "stated mass is one electron mass below the formula",
        "01030": "stated mass is one H (or H+) above the formula",
        "01032": "stated mass is one H (or H+) above the formula",
        "01033": "stated mass is -8.0502 Da from the formula",
        "01034": "stated mass is -8.0502 Da from the formula",
        "01038": "stated mass is one H (or H+) above the formula",
        "01039": "stated mass uses an old 2H mass (+3.5e-5 Da per D)",
        "01040": "stated mass is +1.0082 Da from the formula",
        "01041": "stated mass uses an old 2H mass (+3.5e-5 Da per D)",
        "01042": "stated mass is +1.0082 Da from the formula",
        "01043": "stated mass is one electron mass below the formula",
        "01044": "stated mass is one electron mass below the formula",
        "01045": "stated mass is one electron mass below the formula",
        "01046": "stated mass is one H (or H+) above the formula",
        "01047": "stated mass is one electron mass below the formula",
        "01048": "stated mass is one H (or H+) above the formula",
        "01049": "stated mass is one electron mass below the formula",
        "01050": "stated mass is one H (or H+) above the formula",
        "01051": "stated mass uses an old 2H mass (+3.5e-5 Da per D)",
        "01052": "stated mass uses an old 2H mass (+3.5e-5 Da per D)",
        "01053": "stated mass is 0.0055 Da above the formula (d6 mass shift)",
        "01054": "stated mass is 0.0055 Da above the formula (d6 mass shift)",
        "01055": "stated mass is one electron mass below the formula",
        "01056": "stated mass is one electron mass below the formula",
        "01074": "stated mass is -1.0316 Da from the formula",
        "01094": "stated mass includes H2O the formula omits",
        "01095": "stated mass includes H2O the formula omits",
        "02003": "formula lists D10/D6 where the d12/d8 mass needs two more D",
        "02030": "formula lists D10/D6 where the d12/d8 mass needs two more D",
        "02043": "stated mass is one electron mass below the formula",
        "02044": "stated mass is -1.0078 Da from the formula",
        "02048": "formula lists D10/D6 where the d12/d8 mass needs two more D",
        "02049": "formula lists D10/D6 where the d12/d8 mass needs two more D",
        "02050": "formula lists D10/D6 where the d12/d8 mass needs two more D",
        "02052": "stated mass is one H (or H+) above the formula",
        "02053": "stated mass is one electron mass below the formula",
        "02054": "stated mass is one electron mass below the formula",
        "02055": "stated mass is one electron mass below the formula",
        "02056": "stated mass is one electron mass below the formula",
        "02064": "stated mass is -2.0162 Da from the formula",
        "02135": "stated mass is +5.0391 Da from the formula",
        "03001": "stated mass is one electron mass below the formula",
        "03009": "formula copied from PDH-d10; mass is for NNP9",
    },
    "uniprot_ptm": {
        "0741": "MM 104.0261 is 1.2e-4 Da below C7H4O (104.026215)",
    },
    "gno": {},
}

# Upstream rounds some stated masses to four decimals (PSI-MOD, XLMOD, UniProt MM).
COMPOSITION_TOL = {"unimod": 1e-5, "psimod": 1e-4, "resid": 1e-4, "xlmod": 1e-4, "uniprot_ptm": 1e-4, "gno": TOL}


ELECTRON_MASS = 0.000548579909


def _agrees(calc, stated, tol, source):
    # Charged entries state the mass of the ion: composition minus one electron per positive
    # charge (quaternary ammonium, PSI-MOD "C 3 H 7 1+") or plus one per negative charge
    # (iron-sulfur clusters, "Fe 4 H -4 S 4 2-").
    # Only PSI-MOD (and RESID, which is read from it) and UniProt record charged entries.
    charges = range(-4, 5) if source in ("psimod", "resid", "uniprot_ptm") else (0,)
    return any(abs(calc - k * ELECTRON_MASS - stated) <= tol for k in charges)


@pytest.mark.parametrize("source", list(BUNDLED))
def test_ontology_mass_matches_composition(source):
    tol = COMPOSITION_TOL[source]
    known = KNOWN_UPSTREAM_MISMATCHES[source]
    wrong = {}
    for key, info in BUNDLED[source].items():
        if not info.dict_composition or info.monoisotopic_mass is None:
            continue
        calc = _mass(dict(info.dict_composition))
        if not _agrees(calc, info.monoisotopic_mass, tol, source) and key not in known:
            wrong[key] = (info.name, info.formula, info.monoisotopic_mass, round(calc, 6))
    assert not wrong, f"{len(wrong)} {source} masses disagree with composition: {list(wrong.items())[:5]}"
    stale = [
        k
        for k in known
        if _agrees(
            _mass(dict(BUNDLED[source][k].dict_composition or {})), BUNDLED[source][k].monoisotopic_mass, tol, source
        )
    ]
    assert not stale, f"known mismatches now agree, drop them from the list: {stale}"


# --- amino acids ------------------------------------------------------------------------


@pytest.mark.parametrize("code", sorted(AMINO_ACIDS))
def test_amino_acid_residue_matches_unimod(code):
    ref = AMINO_ACIDS[code]
    info = AMINO_ACID_INFOS[code]
    assert {k: v for k, v in (info.dict_composition or {}).items() if v} == ref["composition"]
    assert info.monoisotopic_mass == pytest.approx(ref["mono"], abs=TOL)
    assert info.average_mass == pytest.approx(ref["avg"], abs=TOL)


# --- UniProt ptmlist refresh --------------------------------------------------------------


def test_uniprot_glycan_masses_not_swapped():
    # ptmlist before 2026_03 had MM and MA exchanged for glycan entries such as PTM-0745.
    info = UNIPROT_PTM_MODIFICATIONS["0745"]
    assert info.monoisotopic_mass == pytest.approx(1298.47596, abs=1e-5)
    assert info.average_mass is not None and info.average_mass > info.monoisotopic_mass
