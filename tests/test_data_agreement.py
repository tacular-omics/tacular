"""Cross-check tacular's bundled UNIMOD and PSI-MOD data against unimodpy and psimodpy.

unimodpy and psimodpy parse the same OBO releases independently, so every entry's
monoisotopic mass and composition should agree. A failure lists every disagreeing entry;
fix the cause (a parser bug on either side, or a data-version drift), do not loosen the
comparison. Skipped when the packages are not installed (they are dev-only dependencies).
"""

import math
import warnings

import pytest

from tacular.psimod.data import PSI_MODIFICATIONS
from tacular.psimod.data import VERSION as PSIMOD_VERSION
from tacular.unimod.data import UNIMOD_MODIFICATIONS
from tacular.unimod.data import VERSION as UNIMOD_VERSION

MASS_ABS_TOL = 1e-6


def _header_value(header_lines, key: str) -> str | None:
    prefix = f"{key}:"
    for line in header_lines:
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _mismatches(tacular_data, get_entry, mass_attr: str) -> list[str]:
    problems = []
    for raw_id, info in tacular_data.items():
        entry = get_entry(int(raw_id))
        if entry is None:
            problems.append(f"{raw_id} {info.name!r}: missing from the reference package")
            continue
        mass = getattr(entry, mass_attr)
        if (mass is None) != (info.monoisotopic_mass is None) or (
            mass is not None and not math.isclose(mass, info.monoisotopic_mass, rel_tol=0, abs_tol=MASS_ABS_TOL)
        ):
            problems.append(f"{raw_id} {info.name!r}: mass tacular={info.monoisotopic_mass} reference={mass}")
        composition = dict(entry.dict_composition or {})
        if composition != dict(info.dict_composition or {}):
            problems.append(
                f"{raw_id} {info.name!r}: composition tacular={dict(info.dict_composition or {})} "
                f"reference={composition}"
            )
    return problems


@pytest.fixture(scope="module")
def unimod_db():
    unimodpy = pytest.importorskip("unimodpy")
    return unimodpy.load()


@pytest.fixture(scope="module")
def psimod_db():
    psimodpy = pytest.importorskip("psimodpy")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        return psimodpy.load()


def test_unimod_same_data_version(unimod_db):
    assert _header_value(unimod_db.header_lines, "date") == UNIMOD_VERSION


def test_psimod_same_data_version(psimod_db):
    assert _header_value(psimod_db.header_lines, "data-version") == PSIMOD_VERSION


def test_unimod_masses_and_compositions_agree(unimod_db):
    problems = _mismatches(UNIMOD_MODIFICATIONS, unimod_db.get_by_id, "delta_mono_mass")
    assert not problems, f"{len(problems)} UNIMOD mismatches:\n" + "\n".join(problems)


def test_psimod_masses_and_compositions_agree(psimod_db):
    problems = _mismatches(PSI_MODIFICATIONS, psimod_db.get_by_id, "diff_mono")
    assert not problems, f"{len(problems)} PSI-MOD mismatches:\n" + "\n".join(problems)


def test_unimod_covers_every_reference_entry(unimod_db):
    # UNIMOD:0 is the ontology root node, which has no mass
    missing = [e.id for e in unimod_db if e.id != 0 and str(e.id) not in UNIMOD_MODIFICATIONS]
    assert not missing


def test_psimod_covers_every_live_entry_with_a_mass(psimod_db):
    # tacular keeps non-obsolete entries that have a mass difference
    missing = [
        e.id
        for e in psimod_db
        if not e.is_obsolete and e.diff_mono is not None and f"{e.id:05d}" not in PSI_MODIFICATIONS
    ]
    assert not missing
