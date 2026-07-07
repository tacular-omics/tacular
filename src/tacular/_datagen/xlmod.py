"""Build XLMOD ``XlModInfo`` objects from an ``XLMod.obo`` file.

Ported from ``data_gen/generator/gen_xlmod.py`` (parsing only; no ``.py``
rendering). Includes the isotope-composition fix: isotope-labelled atoms are
re-added under their isotope key (e.g. ``13C``) so ``dict_composition`` and
``formula`` stay consistent with ``monoisotopic_mass``.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..elements import ELEMENT_LOOKUP
from ..xlmod.dclass import XlModInfo
from ._utils import (
    format_composition_string,
    get_id_and_name,
    get_obo_metadata,
    is_obsolete,
    read_obo,
)

DATA_KEY = "xlmodifications"
JSON_NAME = "xlmodifications.json"
OBO_NAME = "XLMod.obo"
OBO_URL = "https://raw.githubusercontent.com/HUPO-PSI/xlmod-CV/master/XLMOD.obo"

logger = logging.getLogger(__name__)


def _build_term_lookup(terms: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build a lookup dictionary of term_id -> term data for quick access."""
    lookup: dict[str, dict[str, Any]] = {}
    for term in terms:
        term_id, _ = get_id_and_name(term)
        lookup[term_id] = term
    return lookup


def _get_parent_ids(term: dict[str, Any]) -> list[str]:
    """Extract parent term IDs from is_a relationships."""
    parents: list[str] = []
    for is_a in term.get("is_a", []):
        # is_a format: "XLMOD:00001 ! parent term name"
        parent_id = is_a.split("!")[0].strip()
        parents.append(parent_id)
    return parents


def _find_inherited_properties(
    term_id: str, term_lookup: dict[str, dict[str, Any]], visited: set[str] | None = None
) -> tuple[str | None, str | None, str | None]:
    """Walk up the ontology hierarchy to find deadEndFormula, bridgeFormula, or monoIsotopicMass.

    Returns (dead_formula, bridge_formula, mono_mass) from the first ancestor that has them.
    """
    if visited is None:
        visited = set()

    if term_id in visited:
        return None, None, None

    visited.add(term_id)

    term = term_lookup.get(term_id)
    if term is None:
        return None, None, None

    property_values: dict[str, list[str]] = {}
    for val in term.get("property_value", []):
        elems = val.split('"')
        if len(elems) < 2:
            continue
        k = elems[0].rstrip().replace(":", "")
        v = elems[1].strip()
        property_values.setdefault(k, []).append(v)

    def _extract_single(values: list[Any] | Any) -> Any:
        if isinstance(values, list):
            if len(values) == 0:
                return None
            val = values[0]
        else:
            val = values
        return None if val is None else val

    dead_formula = _extract_single(property_values.get("deadEndFormula", [None]))
    bridge_formula = _extract_single(property_values.get("bridgeFormula", [None]))
    mono_mass = _extract_single(property_values.get("monoIsotopicMass", [None]))

    if dead_formula or bridge_formula or mono_mass:
        return dead_formula, bridge_formula, mono_mass

    parent_ids = _get_parent_ids(term)
    for parent_id in parent_ids:
        dead, bridge, mono = _find_inherited_properties(parent_id, term_lookup, visited)
        if dead or bridge or mono:
            return dead, bridge, mono

    return None, None, None


def _entries(terms: list[dict[str, Any]]) -> Iterator[XlModInfo]:
    # Build lookup table for quick term access
    term_lookup = _build_term_lookup(terms)

    for term in terms:
        term_id, term_name = get_id_and_name(term)
        full_term_id = term_id  # Keep the full "XLMOD:00001" format for lookup
        term_id = term_id.replace("XLMOD:", "")

        if is_obsolete(term):
            continue

        property_values: dict[str, list[str]] = {}
        for val in term.get("property_value", []):
            elems = val.split('"')
            if len(elems) < 2:
                continue
            k = elems[0].rstrip().replace(":", "")
            v = elems[1].strip()
            property_values.setdefault(k, []).append(v)

        def _extract_single(values: list[Any] | Any) -> Any:
            if isinstance(values, list):
                if len(values) == 0:
                    return None
                val = values[0]
            else:
                val = values
            return None if val is None else val

        dead_formula = _extract_single(property_values.get("deadEndFormula", [None]))
        bridge_formula = _extract_single(property_values.get("bridgeFormula", [None]))
        mono_mass = _extract_single(property_values.get("monoIsotopicMass", [None]))

        # If missing properties, try to inherit from parent terms
        if not dead_formula and not bridge_formula and not mono_mass:
            inherited_dead, inherited_bridge, inherited_mono = _find_inherited_properties(full_term_id, term_lookup)
            if inherited_dead or inherited_bridge or inherited_mono:
                dead_formula = dead_formula or inherited_dead
                bridge_formula = bridge_formula or inherited_bridge
                mono_mass = mono_mass or inherited_mono

        # attempt to find any average/avg mass property if present
        avg_mass = None
        for k in property_values.keys():
            if "avg" in k.lower() or "average" in k.lower():
                avg_mass = _extract_single(property_values.get(k, [None]))
                break

        raw_formula = dead_formula or bridge_formula

        formula: str | None = None
        composition: dict[str, int] | None = None
        calc_mono: float | None = None
        calc_avg: float | None = None

        if isinstance(raw_formula, str) and raw_formula.strip() != "":
            try:
                # Directly parse space-separated tokens into elemental counts.
                # Tokens examples: 'C8', 'H12', '13C6', 'D4', '-C1', '-H2'
                parts = raw_formula.split()
                base_counts: dict[str, int] = defaultdict(int)
                isotope_counts: dict[tuple[str, int], int] = defaultdict(int)

                for token in parts:
                    if not token:
                        continue

                    neg = False
                    tkn = token
                    if tkn.startswith("-"):
                        neg = True
                        tkn = tkn[1:]

                    # match leading isotope like '13C6' or '13C'
                    m_iso = re.match(r"^(\d+)([A-Za-z][a-z]?)(\d*)$", tkn)
                    if m_iso:
                        iso_str, elem, cnt_str = m_iso.groups()
                        cnt = int(cnt_str) if cnt_str else 1
                        if neg:
                            cnt = -cnt
                        iso = int(iso_str)
                        isotope_counts[(elem, iso)] += cnt
                        base_counts[elem] += cnt
                        continue

                    # match regular element like 'C6' or 'D4' or 'C' or 'C-1'
                    m_elem = re.match(r"^([A-Za-z][a-z]?)(-?\d*)$", tkn)
                    if m_elem:
                        elem_sym, cnt_str = m_elem.groups()
                        if cnt_str == "" or cnt_str == "-":
                            cnt = 1 if cnt_str == "" else -1
                        else:
                            cnt = int(cnt_str)
                        if neg:
                            cnt = -cnt
                        base_counts[elem_sym] += cnt
                        continue

                    # fallback: unrecognized token
                    raise ValueError(f"Unrecognized token in XLMOD formula: '{token}'")

                # Build composition dict (subtract isotope-specified counts later)
                composition = dict(base_counts)

                # Calculate masses accounting for isotope-specific counts
                comp_mono = 0.0
                comp_avg = 0.0
                for (elem_sym, iso), iso_count in isotope_counts.items():
                    comp_mono += ELEMENT_LOOKUP.mass(f"{iso}{elem_sym}") * iso_count
                    comp_avg += ELEMENT_LOOKUP.mass(f"{iso}{elem_sym}") * iso_count
                    composition[elem_sym] = composition.get(elem_sym, 0) - iso_count

                for elem_sym, cnt in composition.items():
                    if cnt == 0:
                        continue
                    comp_mono += ELEMENT_LOOKUP.mass(elem_sym, monoisotopic=True) * cnt
                    comp_avg += ELEMENT_LOOKUP.mass(elem_sym, monoisotopic=False) * cnt

                calc_mono = comp_mono
                calc_avg = comp_avg

                # Re-add isotope-specified atoms under their isotope key (e.g. "13C") so the
                # emitted composition/formula reflect them (masses already summed above).
                for (elem_sym, iso), iso_count in isotope_counts.items():
                    composition[f"{iso}{elem_sym}"] = composition.get(f"{iso}{elem_sym}", 0) + iso_count

                # ensure composition is a plain dict (no zero entries)
                composition = {k: v for k, v in composition.items() if v != 0}
                # canonical formula string
                formula = format_composition_string(composition)
            except Exception:
                logger.warning("[XLMOD] Error parsing formula for %s %s: %s", term_id, term_name, raw_formula)
                formula = None
                composition = None
                calc_mono = None
                calc_avg = None

        # Convert reported mono/avg mass to float if present
        reported_mono: float | None = None
        reported_avg: float | None = None
        if mono_mass is not None:
            try:
                reported_mono = float(mono_mass)
            except Exception:
                reported_mono = None
        if avg_mass is not None:
            try:
                reported_avg = float(avg_mass)
            except Exception:
                reported_avg = None

        # skip entries with no formula and no masses
        if (
            formula is None
            and reported_mono is None
            and reported_avg is None
            and calc_mono is None
            and calc_avg is None
        ):
            continue

        yield XlModInfo(
            id=term_id,
            name=term_name,
            formula=formula,
            monoisotopic_mass=float(reported_mono)
            if reported_mono is not None
            else (calc_mono if calc_mono is not None else None),
            average_mass=float(reported_avg)
            if reported_avg is not None
            else (calc_avg if calc_avg is not None else None),
            dict_composition=(composition if isinstance(composition, dict) and composition else None),
        )


def build(obo_path: str | Path) -> tuple[str, list[XlModInfo]]:
    """Parse ``obo_path`` and return ``(version, infos)``."""
    with open(obo_path) as f:
        version = get_obo_metadata(f).get("data-version", "unknown")
        terms = read_obo(f)
    return version, list(_entries(terms))
