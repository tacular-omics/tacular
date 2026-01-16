import os
import re
from collections import Counter
from collections.abc import Generator
from typing import Any

from constants import OutputFile
from logging_utils import setup_logger
from utils import calculate_mass, get_id_and_name, get_obo_metadata, is_obsolete, read_obo

import tacular as pt

logger = setup_logger(__name__, os.path.splitext(os.path.basename(__file__))[0])


# Glycan monosaccharide compositions (from peptacular)
GLYCAN_COMPOSITIONS = {
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


def _parse_glycan_composition(composition_str: str) -> Counter | None:
    """Parse GNO composition format like 'Hex(2)HexNAc(1)' into elemental composition."""
    try:
        tokens = re.findall(r"([A-Za-z0-9]+)\((\d+)\)", composition_str)
        total_composition = Counter()

        for symbol, count in tokens:
            if symbol not in GLYCAN_COMPOSITIONS:
                logger.warning(f"Unknown glycan symbol: {symbol}")
                return None

            glycan_comp = GLYCAN_COMPOSITIONS[symbol]
            for elem, c in glycan_comp.items():
                total_composition[elem] += c * int(count)

        return total_composition
    except Exception as e:
        logger.warning(f"Error parsing glycan composition '{composition_str}': {e}")
        return None


def _composition_to_formula(composition: Counter) -> str:
    """Convert Counter to formula string like 'C20H33N3O15'."""
    # Order: C, H, N, O, then alphabetically
    priority = ["C", "H", "N", "O"]
    parts = []

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


def _get_gno_entries(
    terms: list[dict[str, Any]],
) -> Generator[pt.GnoInfo, None, None]:
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
                        "[GNO] Error calculating mass for %s %s: %s",
                        term_id,
                        term_name,
                        e,
                    )

        if formula is None and mono_mass is None and avg_mass is None:
            logger.debug(f"  ⚠️  Skipping GNO entry with no formula or masses: {term_id} {term_name}")
            continue

        yield pt.GnoInfo(
            id=term_id,
            name=term_name,
            formula=formula,
            monoisotopic_mass=mono_mass,
            average_mass=avg_mass,
            dict_composition=composition_dict,
        )


def gen_gno(output_file: str = OutputFile.GNO):
    logger.info("\n" + "=" * 60)
    logger.info("GENERATING GNO DATA")
    logger.info("=" * 60)

    logger.info("  📖 Reading from: data_gen/data/gno.obo")
    with open("./data/GNOme.obo") as f:
        data = read_obo(f)
        metadata = get_obo_metadata(f)

    version = metadata.get("data-version", "unknown")
    logger.info(f"  ℹ️  Version: {version}")

    gno_entries = list(_get_gno_entries(data))
    logger.info(f"  ✓ Parsed {len(gno_entries)} GNO entries")

    # Print stats
    missing_mono = sum(1 for mod in gno_entries if mod.monoisotopic_mass is None)
    missing_avg = sum(1 for mod in gno_entries if mod.average_mass is None)
    missing_formula = sum(1 for mod in gno_entries if mod.formula is None)

    if missing_mono > 0 or missing_avg > 0 or missing_formula > 0:
        logger.warning("\n  ⚠️  Data Completeness:")
        if missing_mono > 0:
            logger.warning(f"      Missing monoisotopic mass: {missing_mono}")
        if missing_avg > 0:
            logger.warning(f"      Missing average mass: {missing_avg}")
        if missing_formula > 0:
            logger.warning(f"      Missing formula: {missing_formula}")

    logger.info(f"\n  📝 Writing to: {output_file}")

    # Generate the GNO entries
    entries: list[str] = []
    for mod in gno_entries:
        formula_str = f'"{mod.formula}"' if mod.formula is not None else "None"

        entry = f'''        "{mod.id}": GnoInfo(
        id="{mod.id}",
        name="{mod.name}",
        formula={formula_str},
        monoisotopic_mass={mod.monoisotopic_mass},
        average_mass={mod.average_mass},
        dict_composition={mod.dict_composition},
    ),'''
        entries.append(entry)

    entries_str = "\n".join(entries)

    # Write the complete file
    content = f'''"""Auto-generated GNO data"""
# DO NOT EDIT - generated by gen_gno.py

import warnings

from .dclass import GnoInfo

VERSION = "{version}"

try:
    GNO_GLYCANS: dict[str, GnoInfo] = {{
{entries_str}
    }}

    GNO_NAME_TO_ID: dict[str, str] = {{
        glycan.name: glycan.id
        for glycan in GNO_GLYCANS.values()
    }}
except Exception as e:
    warnings.warn(
        f"Exception in gno_data: {{e}}. Using empty dictionaries.",
        UserWarning,
        stacklevel=2
    )
    GNO_GLYCANS: dict[str, GnoInfo] = {{}}
    GNO_NAME_TO_ID: dict[str, str] = {{}}
'''

    with open(output_file, "w") as f:
        f.write(content)

    logger.info(f"✅ Successfully generated {output_file}")
    logger.info(f"   Total entries: {len(gno_entries)}")


if __name__ == "__main__":
    gen_gno()
