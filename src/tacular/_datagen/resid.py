"""Build RESID ``ResidInfo`` objects from a ``PSI-MOD.obo`` file.

Ported from ``data_gen/generator/gen_resid.py`` (parsing only; no ``.py``
rendering). RESID entries are embedded inside PSI-MOD term definitions
(``RESID:AA0001``-style xrefs), so this reads the same ``PSI-MOD.obo`` source
as :mod:`tacular._datagen.psimod`. Matches upstream behavior: duplicate RESID
ids are dropped entirely, and entries with no formula/masses/composition are
dropped, mirroring the filters ``gen_resid.py`` applied when rendering the
bundled module.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..resid.dclass import ResidInfo
from ._utils import (
    calculate_mass,
    get_id_and_name,
    get_obo_metadata,
    is_obsolete,
    parse_formula_to_dict,
    read_obo,
)

DATA_KEY = "resid_modifications"
JSON_NAME = "resid_modifications.json"
OBO_NAME = "PSI-MOD.obo"
OBO_URL = "https://raw.githubusercontent.com/HUPO-PSI/psi-mod-CV/master/PSI-MOD.obo"

logger = logging.getLogger(__name__)

_RESID_ID_RE = re.compile(r"RESID:(AA\d+)(?:#\w+)?")


def _entries(terms: list[dict[str, Any]]) -> Iterator[ResidInfo]:
    for term in terms:
        term_id, term_name = get_id_and_name(term)

        if is_obsolete(term):
            continue

        # Extract RESID IDs from definition field
        definition = term.get("def", [None])[0]
        if not definition:
            continue

        # Extract RESID:AA0001 from definition
        resid_matches = _RESID_ID_RE.findall(str(definition))

        if not resid_matches:
            continue

        # Extract xref property values
        property_values: dict[str, list[str]] = {}
        for val in term.get("xref", []):
            elems = val.split('"')
            if len(elems) < 2:
                # Try colon split for values like "Origin: S"
                parts = val.split(":", 1)
                if len(parts) == 2:
                    k = parts[0].strip()
                    v = parts[1].strip()
                    property_values.setdefault(k, []).append(v)
                continue

            k = elems[0].rstrip().replace(":", "").strip()
            v = elems[1].strip()
            property_values.setdefault(k, []).append(v)

        # Helper to extract a single value from lists
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

            # PSI-MOD format: "C 16 H 28 N 0 O 1"
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
                        "[RESID] Error parsing formula for %s %s: DiffFormula=%r -> generated %r: %s: %s",
                        resid_matches[0],
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

        # Yield one entry per RESID ID found
        for resid_id in resid_matches:
            yield ResidInfo(
                id=resid_id,
                name=term_name,
                formula=formula,
                monoisotopic_mass=mono_mass,
                average_mass=avg_mass,
                dict_composition=composition,
            )


def build(obo_path: str | Path) -> tuple[str, list[ResidInfo]]:
    """Parse ``obo_path`` and return ``(version, infos)``."""
    with open(obo_path) as f:
        version = get_obo_metadata(f).get("data-version", "unknown")
        terms = read_obo(f)

    resid_entries = list(_entries(terms))

    # Drop RESID ids that appear more than once, matching upstream dedup behavior.
    seen_ids: set[str] = set()
    dup_ids: set[str] = set()
    for mod in resid_entries:
        if mod.id in seen_ids:
            dup_ids.add(mod.id)
        seen_ids.add(mod.id)
    resid_entries = [mod for mod in resid_entries if mod.id not in dup_ids]

    infos = [
        mod
        for mod in resid_entries
        if not (
            mod.formula is None
            and mod.monoisotopic_mass is None
            and mod.average_mass is None
            and mod.dict_composition is None
        )
    ]
    return version, infos
