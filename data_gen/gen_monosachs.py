import os
from collections.abc import Generator
from typing import Any

from constants import OutputFile
from logging_utils import setup_logger
from utils import calculate_mass, get_id_and_name, is_obsolete, parse_formula_to_dict, read_obo

import tacular as pt

logger = setup_logger(__name__, os.path.splitext(os.path.basename(__file__))[0])


def _get_monosaccharide_entries(
    terms: list[dict[str, Any]],
) -> Generator[pt.MonosaccharideInfo, None, None]:
    for term in terms:
        term_id, term_name = get_id_and_name(term)
        term_id = term_id.replace("MONO:", "")

        if is_obsolete(term):
            continue

        property_values: dict[str, list[str]] = {}
        for val in term.get("property_value", []):
            elems = val.split('"')
            k = elems[0].rstrip()
            v = elems[1].strip()

            property_values.setdefault(k, []).append(v)

        # helper to extract a single value from lists coming from OBO properties
        def _extract_single(values: list[Any] | Any, label: str) -> Any:
            if isinstance(values, list):
                if len(values) == 0:
                    return None
                if len(values) > 1:
                    logger.warning("[MONOSACCHARIDES] Multiple %s for %s %s %s", label, term_id, term_name, values)
                val = values[0]
            else:
                val = values
            # treat explicit None placeholders
            return None if val is None else val

        delta_formula = _extract_single(property_values.get("has_chemical_formula", [None]), "delta compositions")
        delta_monoisotopic_mass = _extract_single(
            property_values.get("has_monoisotopic_mass", [None]), "delta mono masses"
        )
        delta_average_mass = _extract_single(property_values.get("has_average_mass", [None]), "delta average masses")

        if delta_formula is not None and not isinstance(delta_formula, str):
            raise ValueError("Invalid formula for %s %s: %r" % (term_id, term_name, delta_formula))

        composition: dict[str, int] | None = parse_formula_to_dict(delta_formula) if delta_formula else None
        # remove elements with zero count
        if composition:
            composition = {k: v for k, v in composition.items() if v != 0}

        comp_mass: float | None = None
        comp_avg_mass: float | None = None

        if composition:
            comp_mass = calculate_mass(composition, monoisotopic=True)
            comp_avg_mass = calculate_mass(composition, monoisotopic=False)

        delta_monoisotopic_mass = float(delta_monoisotopic_mass) if delta_monoisotopic_mass is not None else None
        delta_average_mass = float(delta_average_mass) if delta_average_mass is not None else None

        if delta_monoisotopic_mass is not None and comp_mass is not None:
            # assert that they are equal within 0.01 Da
            if abs(float(delta_monoisotopic_mass) - comp_mass) > 0.01:
                logger.warning(
                    "MONOSACCHARIDE MASS MISMATCH [%s] %s: calculated=%.6f reported=%s Formula=%s",
                    term_id,
                    term_name,
                    comp_mass,
                    delta_monoisotopic_mass,
                    delta_formula,
                )
        if delta_average_mass is not None and comp_avg_mass is not None:
            # assert that they are equal within 0.01 Da
            if abs(float(delta_average_mass) - comp_avg_mass) > 0.01:
                logger.warning(
                    "MONOSACCHARIDE MASS MISMATCH [%s] %s: calculated=%.6f reported=%s Formula=%s",
                    term_id,
                    term_name,
                    comp_avg_mass,
                    delta_average_mass,
                    delta_formula,
                )

        if delta_monoisotopic_mass is None and comp_mass is not None:
            delta_monoisotopic_mass = comp_mass
        if delta_average_mass is None and comp_avg_mass is not None:
            delta_average_mass = comp_avg_mass

        yield pt.MonosaccharideInfo(
            id=term_id,
            name=term_name,
            formula=delta_formula,
            monoisotopic_mass=float(delta_monoisotopic_mass) if delta_monoisotopic_mass else None,
            average_mass=float(delta_average_mass) if delta_average_mass else None,
            dict_composition=composition,
        )


def gen_mono(output_file: str = OutputFile.MONOSACCHARIDES):
    logger.info("\n" + "=" * 60)
    logger.info("GENERATING MONOSACCHARIDE DATA")
    logger.info("=" * 60)

    logger.info("  📖 Reading from: data_gen/data/monosaccharides.obo")
    with open("./data/monosaccharides.obo") as f:
        data = read_obo(f)

    logger.info("  📖 Reading from: data_gen/data/additional_monosaccharides.obo")
    with open("./data/additional_monosaccharides.obo") as f:
        additional_data = read_obo(f)

    data.extend(additional_data)

    monosaccharides = list(_get_monosaccharide_entries(data))
    logger.info("  ✓ Parsed %d monosaccharides", len(monosaccharides))

    logger.info("\n  📝 Writing to: %s", output_file)

    # Generate the monosaccharide entries
    entries: list[str] = []

    # Manual mapping of monosaccharide names to their enum member names
    name_to_enum: dict[str, str] = {
        "a-Hex": "aHex",
        "d-Hex": "dHex",
        "en,a-Hex": "en_aHex",
        "HexNAc(S)": "HexNAcS",
        "Neu5Ac": "NeuAc",
        "Neu5Gc": "NeuGc",
        "phosphate": "Phosphate",
        "sulfate": "Sulfate",
    }

    for ms in monosaccharides:
        # Format formula properly - None without quotes, strings with quotes
        formula_str = f'"{ms.formula}"' if ms.formula is not None else "None"

        # Get enum name from mapping
        enum_name = name_to_enum.get(ms.name, ms.name)

        if enum_name is None:
            raise ValueError(f"Monosaccharide name '{ms.name}' not found in name_to_enum mapping.")

        entry = f'''    Monosaccharide.{enum_name}: MonosaccharideInfo(
        id="{ms.id}",
        name=Monosaccharide.{enum_name},
        formula={formula_str},
        monoisotopic_mass={ms.monoisotopic_mass},
        average_mass={ms.average_mass},
        dict_composition={ms.dict_composition},
    ),'''
        entries.append(entry)

    entries_str = "\n".join(entries)

    enum_to_profora_str: dict[str, str] = {"en_aHex": "en,aHex"}

    # Build Monosaccharide StrEnum entries
    enum_entries: list[str] = []
    for ms in monosaccharides:
        enum_name = name_to_enum.get(ms.name, ms.name)
        enum_str = enum_to_profora_str.get(enum_name, enum_name)
        enum_entries.append(f'    {enum_name} = "{enum_str}"')

    enum_str = "\n".join(enum_entries)

    # Write the complete file
    content = f'''"""Auto-generated monosaccharide data"""
# DO NOT EDIT - generated by gen_monosachs.py

import warnings
from enum import StrEnum

from .dclass import MonosaccharideInfo


class Monosaccharide(StrEnum):
    """Enumeration of monosaccharide names."""
{enum_str}

    @classmethod
    def from_str(cls, name: str) -> "Monosaccharide":
        """Get Monosaccharide enum from string"""
        return cls(name)


try:
    MONOSACCHARIDES: dict[Monosaccharide, MonosaccharideInfo] = {{
{entries_str}
    }}

except Exception as e:
    warnings.warn(
        f"Exception in monosaccharides_data: {{e}}. Using empty dictionaries.",
        UserWarning,
        stacklevel=2
    )
    MONOSACCHARIDES: dict[Monosaccharide, MonosaccharideInfo] = {{}}
'''

    with open(output_file, "w") as f:
        f.write(content)

    logger.info("✅ Successfully generated %s", output_file)
    logger.info("   Total entries: %d", len(monosaccharides))


if __name__ == "__main__":
    gen_mono()
