"""Build GNOme ``GnoInfo`` objects from a ``GNOme.obo`` file.

Ported from ``data_gen/generator/gen_gno.py`` (parsing only; no ``.py``
rendering).
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..gno.dclass import GnoInfo
from ._utils import calculate_mass, get_id_and_name, get_obo_metadata, is_obsolete, read_obo

DATA_KEY = "gnome_modifications"
JSON_NAME = "gnome_modifications.json"
OBO_NAME = "GNOme.obo"
OBO_URL = "https://raw.githubusercontent.com/glygen-glycan-data/GNOme/master/gno.obo"

logger = logging.getLogger(__name__)

# Glycan monosaccharide compositions (from peptacular)
_GLYCAN_COMPOSITIONS: dict[str, Counter[str]] = {
    "Hex": Counter({"C": 6, "H": 10, "O": 5}),
    "HexNAc": Counter({"C": 8, "H": 13, "N": 1, "O": 5}),
    "dHex": Counter({"C": 6, "H": 10, "O": 4}),
    "NeuAc": Counter({"C": 11, "H": 17, "N": 1, "O": 8}),
    "NeuGc": Counter({"C": 11, "H": 17, "N": 1, "O": 9}),
    "Pent": Counter({"C": 5, "H": 8, "O": 4}),
    "HexA": Counter({"C": 6, "H": 8, "O": 6}),
    "Fuc": Counter({"C": 6, "H": 10, "O": 4}),
    "Xyl": Counter({"C": 5, "H": 8, "O": 4}),
    "Phospho": Counter({"H": 1, "O": 3, "P": 1}),
    "Sulpho": Counter({"O": 3, "S": 1}),
}


def _parse_glycan_composition(composition_str: str) -> Counter[str] | None:
    """Parse GNO composition format like 'Hex(2)HexNAc(1)' into elemental composition."""
    try:
        tokens = re.findall(r"([A-Za-z0-9]+)\((\d+)\)", composition_str)
        total_composition: Counter[str] = Counter()

        for symbol, count in tokens:
            if symbol not in _GLYCAN_COMPOSITIONS:
                logger.warning(
                    "Unknown glycan symbol %r in composition %r (known symbols: %s)",
                    symbol,
                    composition_str,
                    sorted(_GLYCAN_COMPOSITIONS),
                )
                return None

            glycan_comp = _GLYCAN_COMPOSITIONS[symbol]
            for elem, c in glycan_comp.items():
                total_composition[elem] += c * int(count)

        return total_composition
    except Exception as e:
        logger.warning(
            "Error parsing glycan composition %r: %s: %s", composition_str, type(e).__name__, e, exc_info=True
        )
        return None


def _composition_to_formula(composition: Counter[str]) -> str:
    """Convert Counter to formula string like 'C20H33N3O15'."""
    # Order: C, H, N, O, then alphabetically
    priority = ["C", "H", "N", "O"]
    parts: list[str] = []

    for elem in priority:
        if elem in composition and composition[elem] > 0:
            count = composition[elem]
            parts.append(f"{elem}{count}" if count > 1 else elem)

    # Add any remaining elements alphabetically
    for elem in sorted(composition.keys()):
        if elem not in priority and composition[elem] > 0:
            count = composition[elem]
            parts.append(f"{elem}{count}" if count > 1 else elem)

    return "".join(parts)


def _entries(terms: list[dict[str, Any]]) -> Iterator[GnoInfo]:
    for term in terms:
        term_id, term_name = get_id_and_name(term)
        term_id = term_id.replace("GNO:", "")

        if is_obsolete(term):
            continue

        # Extract property_value entries
        property_values: dict[str, str] = {}
        for val in term.get("property_value", []):
            try:
                elems = val.split('"')
                if len(elems) < 2:
                    continue
                k = elems[0].rstrip()
                v = elems[1].strip()
                property_values[k] = v
            except (IndexError, AttributeError):
                continue

        # GNO:00000202 is the composition property (e.g., "Hex(2)HexNAc(1)")
        composition_str = property_values.get("GNO:00000202")

        formula = None
        composition_dict = None
        mono_mass = None
        avg_mass = None

        if composition_str:
            glycan_comp = _parse_glycan_composition(composition_str)

            if glycan_comp is not None:
                formula = _composition_to_formula(glycan_comp)
                composition_dict = dict(glycan_comp)

                try:
                    mono_mass = calculate_mass(composition_dict, monoisotopic=True)
                    avg_mass = calculate_mass(composition_dict, monoisotopic=False)
                except Exception as e:
                    logger.warning(
                        "[GNO] Error calculating mass for %s %s (composition=%r): %s: %s",
                        term_id,
                        term_name,
                        composition_dict,
                        type(e).__name__,
                        e,
                        exc_info=True,
                    )

        if formula is None and mono_mass is None and avg_mass is None:
            continue

        yield GnoInfo(
            id=term_id,
            name=term_name,
            formula=formula,
            monoisotopic_mass=mono_mass,
            average_mass=avg_mass,
            dict_composition=composition_dict,
        )


def build(obo_path: str | Path) -> tuple[str, list[GnoInfo]]:
    """Parse ``obo_path`` and return ``(version, infos)``."""
    with open(obo_path) as f:
        version = get_obo_metadata(f).get("data-version", "unknown")
        terms = read_obo(f)
    return version, list(_entries(terms))
