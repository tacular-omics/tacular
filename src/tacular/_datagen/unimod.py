"""Build UNIMOD ``UnimodInfo`` objects from a ``UNIMOD.obo`` file.

Ported from ``data_gen/generator/gen_unimod.py`` (parsing only; no ``.py``
rendering). Includes the isotope-composition fix: isotope-labelled atoms are
re-added under their isotope key (e.g. ``13C``) so ``dict_composition`` and
``formula`` stay consistent with ``monoisotopic_mass``.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..elements import ELEMENT_LOOKUP
from ..unimod.dclass import UnimodInfo
from ._utils import (
    format_composition_string,
    get_id_and_name,
    get_obo_metadata,
    is_obsolete,
    parse_formula_to_dict,
    read_obo,
)

DATA_KEY = "unimodifications"
JSON_NAME = "unimodifications.json"
OBO_NAME = "UNIMOD.obo"
OBO_URL = "https://www.unimod.org/obo/unimod.obo"

# UNIMOD writes glycans as short names; expand to element formulas.
_GLYCAN = {
    "Hex": "C6H10O5",
    "HexNAc": "C8H13N1O5",
    "HexA": "C6H8O6",
    "dHex": "C6H10O4",
    "NeuAc": "C11H17N1O8",
    "Pent": "C5H8O4",
    "HexN": "C6H11N1O4",
    "NeuGc": "C11H17N1O9",
    "sulfate": "H0O3S1",
    "Sulf": "H0O3S1",
    "Ac": "C2H2O",
    "Me": "CH2",
    "Kdn": "C9H14O8",
    "Su": "C4H4O4",
    "Hep": "C7H12O6",
}


def _single(property_values: dict[str, list[str]], key: str) -> str | None:
    vals = property_values.get(key, [])
    return vals[0] if vals else None


def _entries(terms: list[dict[str, Any]]) -> Iterator[UnimodInfo]:
    for term in terms:
        term_id, term_name = get_id_and_name(term)
        term_id = term_id.replace("UNIMOD:", "")

        if is_obsolete(term) or term_name == "unimod root node":
            continue

        property_values: dict[str, list[str]] = {}
        for val in term.get("xref", []):
            elems = val.split('"')
            if len(elems) < 2:
                continue
            property_values.setdefault(elems[0].rstrip(), []).append(elems[1].strip())

        delta_composition = _single(property_values, "delta_composition")
        delta_monoisotopic_mass = _single(property_values, "delta_mono_mass")
        delta_average_mass = _single(property_values, "delta_avge_mass")

        formula: str | None = None
        composition: dict[str, int] | None = None
        comp_mass: float | None = None
        comp_avg_mass: float | None = None

        if delta_composition:
            formula_counts: list[tuple[str, int]] = []
            for comp in delta_composition.split():
                comp = comp.strip()
                if "(" in comp and ")" in comp:
                    key = comp.split("(")[0]
                    count = int(comp.split("(")[1].replace(")", ""))
                else:
                    key, count = comp, 1
                formula_counts.append((_GLYCAN.get(key, key), count))

            base_counts: dict[str, int] = defaultdict(int)
            isotope_counts: dict[tuple[str, int], int] = defaultdict(int)
            for formula_part, cnt in formula_counts:
                if cnt == 0:
                    continue
                part = str(formula_part).strip()
                m = re.match(r"^(\d+)([A-Za-z].*)$", part)
                if m:
                    iso = int(m.group(1))
                    rest = m.group(2)
                    if re.match(r"^[A-Z][a-z]?$", rest):
                        isotope_counts[(rest, iso)] += cnt
                        base_counts[rest] += cnt
                        continue
                    part = rest
                for elem_sym, elem_count in (parse_formula_to_dict(part) if part else {}).items():
                    base_counts[elem_sym] += elem_count * cnt

            composition = dict(base_counts)
            comp_mass = 0.0
            comp_avg_mass = 0.0
            for (elem_sym, iso), iso_count in isotope_counts.items():
                comp_mass += ELEMENT_LOOKUP.mass(f"{iso}{elem_sym}") * iso_count
                comp_avg_mass += ELEMENT_LOOKUP.mass(f"{iso}{elem_sym}") * iso_count
                composition[elem_sym] = composition.get(elem_sym, 0) - iso_count
            for elem_sym, total_count in composition.items():
                if total_count == 0:
                    continue
                comp_mass += ELEMENT_LOOKUP.mass(elem_sym, monoisotopic=True) * total_count
                comp_avg_mass += ELEMENT_LOOKUP.mass(elem_sym, monoisotopic=False) * total_count

            # Re-add isotope-specified atoms under their isotope key (e.g. "13C") after the
            # mass loop so composition/formula reflect them without double-counting mass.
            for (elem_sym, iso), iso_count in isotope_counts.items():
                composition[f"{iso}{elem_sym}"] = composition.get(f"{iso}{elem_sym}", 0) + iso_count
            composition = {k: v for k, v in composition.items() if v != 0}
            formula = format_composition_string(composition)

        mono = float(delta_monoisotopic_mass) if delta_monoisotopic_mass else None
        avg = float(delta_average_mass) if delta_average_mass else None
        if mono is None and comp_mass is not None:
            mono = comp_mass
        if avg is None and comp_avg_mass is not None:
            avg = comp_avg_mass

        if formula is None and mono is None and avg is None:
            continue

        yield UnimodInfo(
            id=term_id,
            name=term_name,
            formula=str(formula) if formula else None,
            monoisotopic_mass=mono,
            average_mass=avg,
            dict_composition=composition if composition else None,
        )


def build(obo_path: str | Path) -> tuple[str, list[UnimodInfo]]:
    """Parse ``obo_path`` and return ``(version, infos)``."""
    with open(obo_path) as f:
        version = get_obo_metadata(f).get("date", "")
        terms = read_obo(f)
    return version, list(_entries(terms))
