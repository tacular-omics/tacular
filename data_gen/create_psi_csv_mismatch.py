import csv
from typing import Any

from generator.utils import calculate_mass, get_id_and_name, is_obsolete, parse_formula_to_dict, read_obo
from logging_utils import setup_logger

logger = setup_logger(__name__, "extract_psimod_mismatches")


def extract_psimod_mismatches():
    """Extract PSI-MOD mass mismatches to CSV file"""

    logger.info("Reading PSI-MOD.obo file...")
    with open("./data/PSI-MOD.obo") as f:
        data = read_obo(f)

    mismatches = []

    for term in data:
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

        def _extract_single(values: list[Any] | Any, label: str) -> Any:
            if isinstance(values, list):
                if len(values) == 0:
                    return None
                if len(values) > 1:
                    logger.warning("[PSI-MOD] Multiple %s for %s %s %s", label, term_id, term_name, values)
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

        if isinstance(delta_composition, str):
            delta_composition_parts = delta_composition.split()

            formula_parts: list[str] = []
            i = 0
            while i < len(delta_composition_parts):
                elem_part = delta_composition_parts[i]

                if i + 1 < len(delta_composition_parts):
                    count_str = delta_composition_parts[i + 1]
                    try:
                        count = int(count_str)
                    except ValueError:
                        count = 1
                        i += 1
                        continue
                    i += 2
                else:
                    count = 1
                    i += 1

                if "(" in elem_part and ")" in elem_part:
                    isotope = elem_part[elem_part.index("(") + 1 : elem_part.index(")")]
                    element = elem_part[elem_part.index(")") + 1 :]

                    if count == 1:
                        formula_parts.append(f"[{isotope}{element}]")
                    elif count == 0:
                        continue
                    else:
                        formula_parts.append(f"[{isotope}{element}{count}]")
                else:
                    element = elem_part
                    if count == 1:
                        formula_parts.append(element)
                    elif count == -1:
                        formula_parts.append(f"{element}-1")
                    elif count == 0:
                        continue
                    elif count < 0:
                        formula_parts.append(f"{element}{count}")
                    else:
                        formula_parts.append(f"{element}{count}")

            formula_str = "".join(formula_parts)

            if formula_str != "":
                try:
                    formula = formula_str
                    composition = parse_formula_to_dict(formula_str)
                except Exception as e:
                    logger.warning(
                        "[PSI-MOD] Error parsing formula for %s %s: %s",
                        term_id,
                        term_name,
                        e,
                    )
                    continue

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

        # Check for mass mismatches
        if formula is not None and composition is not None:
            calc_mono = calculate_mass(composition, monoisotopic=True)
            calc_avg = calculate_mass(composition, monoisotopic=False)

            # Check monoisotopic mismatch
            if mono_mass is not None and abs(calc_mono - mono_mass) > 0.01:
                mismatches.append(
                    {
                        "mod_id": term_id,
                        "modification_name": term_name,
                        "mass_type": "Monoisotopic",
                        "calculated": round(calc_mono, 6),
                        "reported": round(mono_mass, 6),
                        "delta": round(calc_mono - mono_mass, 6),
                        "formula": formula,
                    }
                )

            # Check average mismatch
            if avg_mass is not None and abs(calc_avg - avg_mass) > 0.05:
                mismatches.append(
                    {
                        "mod_id": term_id,
                        "modification_name": term_name,
                        "mass_type": "Average",
                        "calculated": round(calc_avg, 6),
                        "reported": round(avg_mass, 6),
                        "delta": round(calc_avg - avg_mass, 6),
                        "formula": formula,
                    }
                )

    # Write to CSV
    output_file = "./output/psimod_mass_mismatches.csv"
    logger.info(f"Writing {len(mismatches)} mismatches to {output_file}")

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["mod_id", "modification_name", "mass_type", "calculated", "reported", "delta", "formula"]
        )
        writer.writeheader()
        writer.writerows(mismatches)

    logger.info(f"✅ Successfully wrote {len(mismatches)} mismatches to {output_file}")


if __name__ == "__main__":
    extract_psimod_mismatches()
