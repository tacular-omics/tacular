import os
import re
from collections import defaultdict
from collections.abc import Generator
from typing import Any

from constants import OutputFile
from logging_utils import setup_logger
from utils import (
    format_composition_string,
    get_id_and_name,
    is_obsolete,
    parse_formula_to_dict,
    read_obo,
)

import tacular as t

logger = setup_logger(__name__, os.path.splitext(os.path.basename(__file__))[0])


def _get_unimod_entries(
    terms: list[dict[str, Any]],
) -> Generator[t.UnimodInfo, None, None]:
    for term in terms:
        term_id, term_name = get_id_and_name(term)
        term_id = term_id.replace("UNIMOD:", "")

        if is_obsolete(term):
            continue

        if term_name == "unimod root node":
            continue

        property_values: dict[str, list[str]] = {}
        for val in term.get("xref", []):
            elems = val.split('"')
            k = elems[0].rstrip()
            v = elems[1].strip()

            property_values.setdefault(k, []).append(v)

        def _extract_single(values: list[Any] | Any, label: str) -> Any:
            if isinstance(values, list):
                if len(values) == 0:
                    return None
                if len(values) > 1:
                    logger.warning("[UNIMOD] Multiple %s for %s %s %s", label, term_id, term_name, values)
                val = values[0]
            else:
                val = values
            return None if val is None else val

        delta_composition = _extract_single(property_values.get("delta_composition", [None]), "delta compositions")
        delta_monoisotopic_mass = _extract_single(property_values.get("delta_mono_mass", [None]), "delta mono masses")
        delta_average_mass = _extract_single(property_values.get("delta_avge_mass", [None]), "delta average masses")

        # Parse composition if available
        formula = None
        comp_mass: float | None = None
        comp_avg_mass: float | None = None

        if delta_composition:
            components = delta_composition.split()
            formuals_counts: list[tuple[str, int]] = []
            for comp in components:
                if "(" in comp and ")" in comp:
                    key = comp.strip().split("(")[0]
                    count = int(comp.strip().split("(")[1].replace(")", ""))
                else:
                    key = comp.strip()
                    count = 1
                formuals_counts.append((key, count))

            # replace glycan with formulas or canonical equivalents
            for i, (key, count) in enumerate(formuals_counts):
                match key:
                    case "Hex":
                        formuals_counts[i] = ("C6H10O5", count)
                        continue
                    case "HexNAc":
                        formuals_counts[i] = ("C8H13N1O5", count)
                        continue
                    case "HexA":
                        formuals_counts[i] = ("C6H8O6", count)
                        continue
                    case "dHex":
                        formuals_counts[i] = ("C6H10O4", count)
                        continue
                    case "NeuAc":
                        formuals_counts[i] = ("C11H17N1O8", count)
                        continue
                    case "Pent":
                        formuals_counts[i] = ("C5H8O4", count)
                        continue
                    case "HexN":
                        formuals_counts[i] = ("C6H11N1O4", count)
                        continue
                    case "NeuGc":
                        formuals_counts[i] = ("C11H17N1O9", count)
                        continue
                    case "sulfate" | "Sulf":
                        formuals_counts[i] = ("H0O3S1", count)
                        continue
                    case "Ac":
                        formuals_counts[i] = ("C2H2O", count)
                        continue
                    case "Me":
                        formuals_counts[i] = ("CH2", count)
                        continue
                    case "Kdn":
                        formuals_counts[i] = ("C9H14O8", count)
                        continue
                    case "Su":
                        formuals_counts[i] = ("C4H4O4", count)
                        continue
                    case "Hep":
                        formuals_counts[i] = ("C7H12O6", count)
                        continue
                    case _:
                        continue

            # Build element counts, tracking any explicit isotope-specified counts
            base_counts: dict[str, int] = defaultdict(int)
            isotope_counts: dict[tuple[str, int], int] = defaultdict(int)
            try:
                for formula_part, cnt in formuals_counts:
                    if cnt == 0:
                        continue

                    part = str(formula_part).strip()

                    # If part starts with digits (isotope prefix), e.g., '13C' or '15N'
                    m = re.match(r"^(\d+)([A-Za-z].*)$", part)
                    if m:
                        iso = int(m.group(1))
                        rest = m.group(2)
                        # If rest is a simple element symbol (C, N, O, etc.)
                        if re.match(r"^[A-Z][a-z]?$", rest):
                            elem_sym = rest
                            isotope_counts[(elem_sym, iso)] += cnt
                            base_counts[elem_sym] += cnt
                            continue
                        else:
                            # Otherwise treat rest as a formula string and parse normally
                            part = rest

                    # Normal formula or element (e.g., 'C', 'CH2', 'C9H14O8')
                    parsed = parse_formula_to_dict(part) if part else {}
                    for elem_sym, elem_count in parsed.items():
                        base_counts[elem_sym] += elem_count * cnt
            except Exception as e:
                raise ValueError(
                    f"Error parsing composition for Unimod {term_id} {term_name} with formula {delta_composition}: {e}"
                ) from e

            # Merge base_counts into a simple composition dict
            composition = dict(base_counts)

            # Calculate masses accounting for isotopic-specification when present
            comp_mass = 0.0
            comp_avg_mass = 0.0
            # handle isotope-specific contributions
            for (elem_sym, iso), iso_count in isotope_counts.items():
                comp_mass += t.ELEMENT_LOOKUP.mass(f"{iso}{elem_sym}") * iso_count
                comp_avg_mass += t.ELEMENT_LOOKUP.mass(f"{iso}{elem_sym}") * iso_count
                # subtract isotope counts from base_counts since we'll add base (non-isotope) separately
                composition[elem_sym] = composition.get(elem_sym, 0) - iso_count

            # add remaining base (non-isotope-specified) contributions using monoisotopic or average
            for elem_sym, total_count in composition.items():
                if total_count == 0:
                    continue
                comp_mass += t.ELEMENT_LOOKUP.mass(elem_sym, monoisotopic=True) * total_count
                comp_avg_mass += t.ELEMENT_LOOKUP.mass(elem_sym, monoisotopic=False) * total_count

            # canonical formula string
            formula = format_composition_string({k: v for k, v in composition.items() if v != 0})

        delta_monoisotopic_mass = float(delta_monoisotopic_mass) if delta_monoisotopic_mass else None
        delta_average_mass = float(delta_average_mass) if delta_average_mass else None

        # Validate masses if both calculated and reported are available
        if delta_monoisotopic_mass is not None and comp_mass is not None:
            if abs(float(delta_monoisotopic_mass) - comp_mass) > 0.01:
                symbol = "🔴" if abs(float(delta_monoisotopic_mass) - comp_mass) > 1.0 else "⚠️"
                logger.warning(
                    "%s UNIMOD MASS MISMATCH [%s] %s: Mono Mass calculated=%.6f reported=%s Formula=%s Composition=%s",
                    symbol,
                    term_id,
                    term_name,
                    comp_mass,
                    delta_monoisotopic_mass,
                    delta_composition,
                    composition,
                )
        if delta_average_mass is not None and comp_avg_mass is not None:
            if abs(float(delta_average_mass) - comp_avg_mass) > 0.2:
                symbol = "⚠️⚠️" if abs(float(delta_average_mass) - comp_avg_mass) > 1.0 else "⚠️"
                logger.warning(
                    "%s UNIMOD MASS MISMATCH [%s] %s: Avg MMass calculated=%.6f reported=%s Formula=%s Composition=%s",
                    symbol,
                    term_id,
                    term_name,
                    comp_avg_mass,
                    delta_average_mass,
                    delta_composition,
                    composition,
                )

        # Use calculated masses if reported masses are missing
        if delta_monoisotopic_mass is None and comp_mass is not None:
            delta_monoisotopic_mass = comp_mass
        if delta_average_mass is None and comp_avg_mass is not None:
            delta_average_mass = comp_avg_mass

        yield t.UnimodInfo(
            id=term_id,
            name=term_name,
            formula=str(formula) if formula else None,
            monoisotopic_mass=float(delta_monoisotopic_mass) if delta_monoisotopic_mass else None,
            average_mass=float(delta_average_mass) if delta_average_mass else None,
            dict_composition=(composition if isinstance(composition, dict) and composition else None),
        )


def gen_uni(output_file: str = OutputFile.UNIMOD):
    logger.info("\n" + "=" * 60)
    logger.info("GENERATING UNIMOD DATA")
    logger.info("=" * 60)

    logger.info("  📖 Reading from: data_gen/data/unimod.obo")
    with open("./data/unimod.obo") as f:
        data = read_obo(f)

    unimod_entries = list(_get_unimod_entries(data))
    logger.info("  ✓ Parsed %d Unimod entries", len(unimod_entries))

    # print stats on number of entries missing mono avg or formula
    missing_mono = sum(1 for mod in unimod_entries if mod.monoisotopic_mass is None)
    missing_avg = sum(1 for mod in unimod_entries if mod.average_mass is None)
    missing_formula = sum(1 for mod in unimod_entries if mod.formula is None)
    if missing_mono > 0 or missing_avg > 0 or missing_formula > 0:
        logger.warning("\n  ⚠️  Data Completeness:")
        if missing_mono > 0:
            logger.warning("      Missing monoisotopic mass: %d", missing_mono)
        if missing_avg > 0:
            logger.warning("      Missing average mass: %d", missing_avg)
        if missing_formula > 0:
            logger.warning("      Missing formula: %d", missing_formula)

    logger.info("\n  📝 Writing to: %s", output_file)

    # Generate the Unimod entries
    entries: list[str] = []
    for mod in unimod_entries:
        # Format formula properly - None without quotes, strings with quotes
        formula_str = f'"{mod.formula}"' if mod.formula is not None else "None"

        # Format composition properly - None without parse_composition, dict with it
        if mod.dict_composition is not None:
            composition_str = f"parse_composition({mod.dict_composition})"
        else:
            composition_str = "None"

        entry = f'''    "{mod.id}": UnimodInfo(
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
    content = f'''"""Auto-generated Unimod data"""
# DO NOT EDIT - generated by gen_unimod.py

from .dclass import UnimodInfo
import warnings


try:
    UNIMOD_MODIFICATIONS: dict[str, UnimodInfo] = {{
{entries_str}
    }}

    UNIMOD_NAME_TO_ID: dict[str, str] = {{
        mod.name: mod.id
        for mod in UNIMOD_MODIFICATIONS.values()
    }}
except Exception as e:
    warnings.warn(
        f"Exception in unimod_data: {{e}}. Using empty dictionaries.",
        UserWarning,
        stacklevel=2
    )
    UNIMOD_MODIFICATIONS: dict[str, UnimodInfo] = {{}} # type: ignore
    UNIMOD_NAME_TO_ID: dict[str, str] = {{}} # type: ignore
'''

    with open(output_file, "w") as f:
        f.write(content)

    logger.info("✅ Successfully generated %s", output_file)
    logger.info("   Total entries: %d", len(unimod_entries))


if __name__ == "__main__":
    gen_uni()
