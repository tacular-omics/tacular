import os
import re
from collections.abc import Generator
from typing import Any

from constants import OutputFile
from logging_utils import setup_logger
from utils import calculate_mass, get_id_and_name, get_obo_metadata, is_obsolete, parse_formula_to_dict, read_obo

import tacular as pt

logger = setup_logger(__name__, os.path.splitext(os.path.basename(__file__))[0])


def _get_resid_entries(
    terms: list[dict[str, Any]],
) -> Generator[pt.ResidInfo, None, None]:
    for term in terms:
        term_id, term_name = get_id_and_name(term)

        if is_obsolete(term):
            continue

        # Extract RESID IDs from definition field
        definition = term.get("def", [None])[0]
        if not definition:
            continue

        # Extract RESID:AA0001 from definition
        regex_str = r"RESID:(AA\d+)(?:#\w+)?"
        resid_matches = re.findall(regex_str, str(definition))

        if not resid_matches:
            continue

        if len(resid_matches) > 1:
            logger.warning("[RESID] Multiple RESID IDs for %s %s: %s", term_id, term_name, resid_matches)

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
        def _extract_single(values: list[Any] | Any, label: str) -> Any:
            if isinstance(values, list):
                if len(values) == 0:
                    return None
                if len(values) > 1:
                    logger.warning("[RESID] Multiple %s for %s %s %s", label, term_id, term_name, values)
                val = values[0]
            else:
                val = values
            return None if val is None else val

        delta_composition = _extract_single(property_values.get("DiffFormula", [None]), "delta compositions")
        delta_monoisotopic_mass = _extract_single(property_values.get("DiffMono", [None]), "delta mono masses")
        delta_average_mass = _extract_single(property_values.get("DiffAvg", [None]), "delta average masses")

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
                    except ValueError:
                        # If next part is not a number, it's another element
                        count = 1
                        i += 1
                        continue
                    i += 2
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
                    composition: dict[str, int] | None = parse_formula_to_dict(formula_str) if formula_str else None
                    parsed_formula = formula_str
                except Exception as e:
                    logger.warning(
                        "[RESID] Error parsing formula for %s %s: %s -> %s, %s",
                        resid_matches[0],
                        term_name,
                        delta_composition,
                        formula_str,
                        e,
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

        # Validate formula masses against provided masses
        if parsed_formula is not None:
            if composition is None:
                raise ValueError("Composition should not be None if parsed_formula is set")

            calc_mono = calculate_mass(composition, monoisotopic=True)
            calc_avg = calculate_mass(composition, monoisotopic=False)

            if mono_mass is not None and abs(calc_mono - mono_mass) > 0.01:
                symbol = "🔴" if abs(calc_mono - mono_mass) > 1.0 else "⚠️"
                logger.warning(
                    "%s RESID MASS MISMATCH [%s] %s: Monoisotopic calculated=%.6f reported=%.6f Formula=%s",
                    symbol,
                    resid_matches[0],
                    term_name,
                    calc_mono,
                    mono_mass,
                    str(formula).lstrip("Formula:"),
                )

            if avg_mass is not None and abs(calc_avg - avg_mass) > 0.2:
                symbol = "⚠️⚠️" if abs(calc_avg - avg_mass) > 1.0 else "⚠️"
                logger.warning(
                    "%s RESID MASS MISMATCH [%s] %s: Average calculated=%.6f reported=%.6f Formula=%s",
                    symbol,
                    resid_matches[0],
                    term_name,
                    calc_avg,
                    avg_mass,
                    str(formula).lstrip("Formula:"),
                )

        # Yield one entry per RESID ID found
        for resid_id in resid_matches:
            yield pt.ResidInfo(
                id=resid_id,
                name=term_name,
                formula=formula,
                monoisotopic_mass=mono_mass,
                average_mass=avg_mass,
                dict_composition=composition,
            )


def gen_resid(output_file: str = OutputFile.RESID):
    logger.info("\n" + "=" * 60)
    logger.info("GENERATING RESID DATA")
    logger.info("=" * 60)

    logger.info("  📖 Reading from: data_gen/data/PSI-MOD.obo")
    with open("./data/PSI-MOD.obo") as f:
        data = read_obo(f)
        metadata = get_obo_metadata(f)

    version = metadata.get("data-version", "unknown")
    logger.info(f"  ℹ️  Version: {version}")

    resid_entries = list(_get_resid_entries(data))
    logger.info(f"  ✓ Parsed {len(resid_entries)} RESID entries")

    # Print stats on number of entries missing mono avg or formula
    missing_mono = sum(1 for mod in resid_entries if mod.monoisotopic_mass is None)
    missing_avg = sum(1 for mod in resid_entries if mod.average_mass is None)
    missing_formula = sum(1 for mod in resid_entries if mod.formula is None)

    if missing_mono > 0 or missing_avg > 0 or missing_formula > 0:
        logger.warning("\n  ⚠️  Data Completeness:")
        if missing_mono > 0:
            logger.warning(f"      Missing monoisotopic mass: {missing_mono}")
        if missing_avg > 0:
            logger.warning(f"      Missing average mass: {missing_avg}")
        if missing_formula > 0:
            logger.warning(f"      Missing formula: {missing_formula}")

    logger.info(f"\n  📝 Writing to: {output_file}")

    seen_ids: set[str] = set()
    dup_ids: set[str] = set()
    resid_entries = list(resid_entries)
    starting_entry_count = len(resid_entries)
    for mod in resid_entries:
        if mod.id in seen_ids:
            logger.warning(f"[RESID] Duplicate RESID ID found: {mod.id} {mod.name}")
            dup_ids.add(mod.id)
        seen_ids.add(mod.id)

    # keep only ids with no duplicates
    resid_entries = [mod for mod in resid_entries if mod.id not in dup_ids]
    if len(resid_entries) < starting_entry_count:
        logger.info(f"  ✓ Removed {starting_entry_count - len(resid_entries)} duplicate RESID entries")

    # Generate the RESID entries
    entries: list[str] = []
    for mod in resid_entries:
        # skip terms without formula dn masses
        if (
            mod.formula is None
            and mod.monoisotopic_mass is None
            and mod.average_mass is None
            and mod.dict_composition is None
        ):
            logger.debug(f"  ⚠️  Skipping RESID entry with no formula or masses: {mod.id} {mod.name}")
            continue

        # Format formula properly - None without quotes, strings with quotes
        formula_str = f'"{mod.formula}"' if mod.formula is not None else "None"

        entry = f'''        "{mod.id}": ResidInfo(
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
    content = f'''"""Auto-generated RESID data"""
# DO NOT EDIT - generated by gen_resid.py

import warnings

from .dclass import ResidInfo

VERSION = "{version}"

try:
    RESID_MODIFICATIONS: dict[str, ResidInfo] = {{
{entries_str}
    }}

    RESID_NAME_TO_ID: dict[str, str] = {{
        mod.name: mod.id
        for mod in RESID_MODIFICATIONS.values()
    }}
except Exception as e:
    warnings.warn(
        f"Exception in resid_data: {{e}}. Using empty dictionaries.",
        UserWarning,
        stacklevel=2
    )
    RESID_MODIFICATIONS: dict[str, ResidInfo] = {{}}
    RESID_NAME_TO_ID: dict[str, str] = {{}}
'''

    with open(output_file, "w") as f:
        f.write(content)

    logger.info(f"✅ Successfully generated {output_file}")
    logger.info(f"   Total entries: {len(resid_entries)}")


if __name__ == "__main__":
    gen_resid()
