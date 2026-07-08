"""Build PSI-MOD ``PsimodInfo`` objects from a ``PSI-MOD.obo`` file.

Ported from ``data_gen/generator/gen_psimod.py`` (parsing only; no ``.py``
rendering). Entries with no formula/masses/composition are dropped, matching
the filter that ``gen_psimod.py`` applied when rendering the bundled module.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..psimod.dclass import PsimodInfo
from ._utils import (
    calculate_mass,
    get_id_and_name,
    get_obo_metadata,
    is_obsolete,
    parse_formula_to_dict,
    read_obo,
)

DATA_KEY = "psimodifications"
JSON_NAME = "psimodifications.json"
OBO_NAME = "PSI-MOD.obo"
OBO_URL = "https://raw.githubusercontent.com/HUPO-PSI/psi-mod-CV/master/PSI-MOD.obo"

logger = logging.getLogger(__name__)


def _entries(terms: list[dict[str, Any]]) -> Iterator[PsimodInfo]:
    for term in terms:
        term_id, term_name = get_id_and_name(term)
        term_id = term_id.replace("MOD:", "")

        if is_obsolete(term):
            continue

        property_values: dict[str, list[str]] = {}
        for val in term.get("xref", []):
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

        delta_composition = _extract_single(property_values.get("DiffFormula", [None]))
        delta_monoisotopic_mass = _extract_single(property_values.get("DiffMono", [None]))
        delta_average_mass = _extract_single(property_values.get("DiffAvg", [None]))

        # Check if values are 'none'
        if delta_monoisotopic_mass == "none":
            delta_monoisotopic_mass = None

        if delta_average_mass == "none":
            delta_average_mass = None

        if delta_composition == "none":
            delta_composition = None

        # Parse composition if available
        formula = None
        composition = None
        parsed_formula = None

        if isinstance(delta_composition, str):
            delta_composition_parts = delta_composition.split()

            # PSI-MOD format: "(12)C 7 H 12 (14)N 2 (16)O 1"
            # Parse element/isotope and count pairs
            formula_parts: list[str] = []
            i = 0
            while i < len(delta_composition_parts):
                elem_part = delta_composition_parts[i]

                # Get the count (next element in list)
                if i + 1 < len(delta_composition_parts):
                    count_str = delta_composition_parts[i + 1]
                    try:
                        count = int(count_str)
                        i += 2
                    except ValueError:
                        # Next part is another element, not a count: this element is implicitly 1.
                        count = 1
                        i += 1
                else:
                    count = 1
                    i += 1

                # Parse element with optional isotope: "(12)C" or "H" or "(13)C"
                if "(" in elem_part and ")" in elem_part:
                    # Has isotope notation like "(12)C"
                    isotope = elem_part[elem_part.index("(") + 1 : elem_part.index(")")]
                    element = elem_part[elem_part.index(")") + 1 :]

                    # Format as "[13C6]" for isotope notation, with count inside brackets
                    if count == 1:
                        formula_parts.append(f"[{isotope}{element}]")
                    elif count == 0:
                        continue  # skip zero counts
                    else:
                        # All counts (positive, negative, -1) go inside brackets
                        formula_parts.append(f"[{isotope}{element}{count}]")
                else:
                    # Regular element like "H" or "O"
                    element = elem_part
                    if count == 1:
                        formula_parts.append(element)
                    elif count == -1:
                        formula_parts.append(f"{element}-1")
                    elif count == 0:
                        continue  # skip zero counts
                    elif count < 0:
                        formula_parts.append(f"{element}{count}")
                    else:
                        formula_parts.append(f"{element}{count}")

            formula_str = "".join(formula_parts)

            if formula_str == "":
                formula_str = ""
                composition = {}
            else:
                try:
                    formula = formula_str
                    composition = parse_formula_to_dict(formula_str) if formula_str else None
                    parsed_formula = formula_str
                except Exception as e:
                    logger.warning(
                        "[PSI-MOD] Error parsing formula for %s %s: DiffFormula=%r -> generated %r: %s: %s",
                        term_id,
                        term_name,
                        delta_composition,
                        formula_str,
                        type(e).__name__,
                        e,
                        exc_info=True,
                    )
                    formula = None
                    composition = None
                    parsed_formula = None

        # Convert mass strings to floats
        mono_mass: float | None = None
        avg_mass: float | None = None

        if delta_monoisotopic_mass is not None and isinstance(delta_monoisotopic_mass, str):
            mono_mass = float(delta_monoisotopic_mass)
        elif isinstance(delta_monoisotopic_mass, float):
            mono_mass = delta_monoisotopic_mass

        if delta_average_mass is not None and isinstance(delta_average_mass, str):
            avg_mass = float(delta_average_mass)
        elif isinstance(delta_average_mass, float):
            avg_mass = delta_average_mass

        # Validate formula masses against provided masses (matches upstream sanity check)
        if parsed_formula is not None:
            if composition is None:
                raise ValueError("Composition should not be None if parsed_formula is set")
            calculate_mass(composition, monoisotopic=True)
            calculate_mass(composition, monoisotopic=False)

        yield PsimodInfo(
            id=term_id,
            name=term_name,
            formula=formula,
            monoisotopic_mass=mono_mass,
            average_mass=avg_mass,
            dict_composition=composition,
        )


def build(obo_path: str | Path) -> tuple[str, list[PsimodInfo]]:
    """Parse ``obo_path`` and return ``(version, infos)``."""
    with open(obo_path) as f:
        version = get_obo_metadata(f).get("data-version", "unknown")
        terms = read_obo(f)

    infos = [
        info
        for info in _entries(terms)
        if not (
            info.formula is None
            and info.monoisotopic_mass is None
            and info.average_mass is None
            and info.dict_composition is None
        )
    ]
    return version, infos
