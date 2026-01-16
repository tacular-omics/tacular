import os
from collections import defaultdict
from collections.abc import Generator
from typing import Any

from constants import OutputFile
from logging_utils import setup_logger
from utils import calculate_mass, format_composition_string, get_id_and_name, get_obo_metadata, is_obsolete, read_obo

import tacular as pt

logger = setup_logger(__name__, os.path.splitext(os.path.basename(__file__))[0])


def _normalize_formula_string(raw: str) -> str:
    """Normalize tokens like '-C1' -> 'C-1' and join parts.

    The XLMOD OBO uses space-separated tokens, e.g. "C1 H2 -S1" or
    "-C1 -H2 O1". This converts those to a flat formula string acceptable
    to parse_formula_to_dict (e.g., "C1H2S-1").
    """
    parts = raw.split()
    out_parts: list[str] = []
    import re

    for p in parts:
        if not p:
            continue
        if p.startswith("-"):
            # Handle negative token like -C1 or -13C6
            m = re.match(r"^-(\d*)([A-Za-z][a-z]?)(\d*)$", p)
            if m:
                iso, elem, cnt = m.groups()
                cnt = cnt or "1"
                out_parts.append(f"{iso}{elem}-{cnt}" if iso else f"{elem}-{cnt}")
                continue
            # Fallback: strip leading - and prepend negative sign to trailing number
            p2 = p[1:]
            # convert C1 -> C-1
            m2 = re.match(r"^(\d*)([A-Za-z][a-z]?)(\d*)$", p2)
            if m2:
                iso, elem, cnt = m2.groups()
                cnt = cnt or "1"
                out_parts.append(f"{iso}{elem}-{cnt}" if iso else f"{elem}-{cnt}")
            else:
                out_parts.append(p2)
        else:
            # Handle tokens that start with digits like '13C6' -> '[13C6]'
            mlead = re.match(r"^(\d+)([A-Za-z][a-z]?)(\d*)$", p)
            if mlead:
                iso, elem, cnt = mlead.groups()
                cnt = cnt or ""
                # create bracketed isotope token for parse_formula_to_dict
                out_parts.append(f"[{iso}{elem}{cnt}]")
            else:
                out_parts.append(p)

    return "".join(out_parts)


def _build_term_lookup(terms: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Build a lookup dictionary of term_id -> term data for quick access."""
    lookup = {}
    for term in terms:
        term_id, _ = get_id_and_name(term)
        lookup[term_id] = term
    return lookup


def _get_parent_ids(term: dict[str, Any]) -> list[str]:
    """Extract parent term IDs from is_a relationships."""
    parents = []
    for is_a in term.get("is_a", []):
        # is_a format: "XLMOD:00001 ! parent term name"
        parent_id = is_a.split("!")[0].strip()
        parents.append(parent_id)
    return parents


def _find_inherited_properties(
    term_id: str, term_lookup: dict[str, dict[str, Any]], visited: set[str] | None = None
) -> tuple[str | None, str | None, str | None]:
    """
    Walk up the ontology hierarchy to find deadEndFormula, bridgeFormula, or monoIsotopicMass.
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

    # Extract properties from current term
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

    # If we found properties, return them
    if dead_formula or bridge_formula or mono_mass:
        return dead_formula, bridge_formula, mono_mass

    # Otherwise, recursively check parent terms
    parent_ids = _get_parent_ids(term)
    for parent_id in parent_ids:
        dead, bridge, mono = _find_inherited_properties(parent_id, term_lookup, visited)
        if dead or bridge or mono:
            logger.info("[XLMOD] Inherited properties from parent %s for term %s", parent_id, term_id)
            return dead, bridge, mono

    return None, None, None


def _get_xlmod_entries(terms: list[dict[str, Any]]) -> Generator[pt.XlModInfo, None, None]:
    # Build lookup table for quick term access
    term_lookup = _build_term_lookup(terms)

    for term in terms:
        term_id, term_name = get_id_and_name(term)
        full_term_id = term_id  # Keep the full "XLMOD:00001" format for lookup
        term_id = term_id.replace("XLMOD:", "")

        if is_obsolete(term):
            continue

        # collect property_value keys
        property_values: dict[str, list[str]] = {}
        for val in term.get("property_value", []):
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
                    logger.warning("[XLMOD] Multiple %s for %s %s %s", label, term_id, term_name, values)
                val = values[0]
            else:
                val = values
            return None if val is None else val

        dead_formula = _extract_single(property_values.get("deadEndFormula", [None]), "deadEndFormula")
        bridge_formula = _extract_single(property_values.get("bridgeFormula", [None]), "bridgeFormula")
        mono_mass = _extract_single(property_values.get("monoIsotopicMass", [None]), "monoIsotopicMass")

        # If missing properties, try to inherit from parent terms
        if not dead_formula and not bridge_formula and not mono_mass:
            inherited_dead, inherited_bridge, inherited_mono = _find_inherited_properties(full_term_id, term_lookup)
            if inherited_dead or inherited_bridge or inherited_mono:
                logger.info("[XLMOD] Inherited properties for %s %s from parent term", term_id, term_name)
                dead_formula = dead_formula or inherited_dead
                bridge_formula = bridge_formula or inherited_bridge
                mono_mass = mono_mass or inherited_mono

        # attempt to find any average/avg mass property if present
        avg_mass = None
        for k in property_values.keys():
            if "avg" in k.lower() or "average" in k.lower():
                avg_mass = _extract_single(property_values.get(k, [None]), "averageMass")
                break

        # ... rest of the existing code continues unchanged ...

        if dead_formula and bridge_formula:
            logger.warning(
                "[XLMOD] Both deadEndFormula and bridgeFormula present for %s %s. Using deadEndFormula.",
                term_id,
                term_name,
            )

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

                import re

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
                    comp_mono += pt.ELEMENT_LOOKUP.mass(f"{iso}{elem_sym}") * iso_count
                    comp_avg += pt.ELEMENT_LOOKUP.mass(f"{iso}{elem_sym}") * iso_count
                    composition[elem_sym] = composition.get(elem_sym, 0) - iso_count

                for elem_sym, cnt in composition.items():
                    if cnt == 0:
                        continue
                    comp_mono += pt.ELEMENT_LOOKUP.mass(elem_sym, monoisotopic=True) * cnt
                    comp_avg += pt.ELEMENT_LOOKUP.mass(elem_sym, monoisotopic=False) * cnt

                calc_mono = comp_mono
                calc_avg = comp_avg

                # canonical formula string (base-only composition)
                formula = format_composition_string({k: v for k, v in composition.items() if v != 0})
                # ensure composition is a plain dict (no zero entries)
                composition = {k: v for k, v in composition.items() if v != 0}
            except Exception as e:
                logger.warning("[XLMOD] Error parsing formula for %s %s: %s -> %s", term_id, term_name, raw_formula, e)
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

        # Validate monoisotopic mass
        if formula is not None and composition is not None and reported_mono is not None and calc_mono is not None:
            if abs(calc_mono - reported_mono) > 0.01:
                symbol = "🔴" if abs(calc_mono - reported_mono) > 0.05 else "⚠️"
                logger.warning(
                    "%s XLMOD MASS MISMATCH [%s] %s: Monoisotopic calculated=%.6f reported=%.6f Formula=%s",
                    symbol,
                    term_id,
                    term_name,
                    calc_mono,
                    reported_mono,
                    raw_formula,
                )

        # Validate average mass (if reported)
        if formula is not None and composition is not None and reported_avg is not None:
            try:
                calc_avg = calculate_mass(composition, monoisotopic=False)
                if abs(calc_avg - reported_avg) > 0.2:
                    symbol = "⚠️⚠️" if abs(calc_avg - reported_avg) > 0.5 else "⚠️"
                    logger.warning(
                        "%s XLMOD AVG MASS MISMATCH [%s] %s: Average calculated=%.6f reported=%.6f Formula=%s",
                        symbol,
                        term_id,
                        term_name,
                        calc_avg,
                        reported_avg,
                        raw_formula,
                    )
            except Exception:
                # ignore calc error
                pass

        # skip entries with no formula and no masses
        if (
            formula is None
            and reported_mono is None
            and reported_avg is None
            and calc_mono is None
            and calc_avg is None
        ):
            logger.debug(f"  ⚠️  Skipping XLMOD entry with no formula or masses: {term_id} {term_name}")
            continue

        yield pt.XlModInfo(
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


def gen_xl(output_file: str = OutputFile.XLMOD):
    logger.info("\n" + "=" * 60)
    logger.info("GENERATING XLMOD DATA")
    logger.info("=" * 60)

    logger.info("  📖 Reading from: data_gen/data/XLMod.obo")
    with open("./data/XLMod.obo") as f:
        data = read_obo(f)
        metadata = get_obo_metadata(f)

    version = metadata.get("data-version", "unknown")
    logger.info(f"  ℹ️  Version: {version}")

    entries_list = list(_get_xlmod_entries(data))
    logger.info("  ✓ Parsed %d XLMOD entries", len(entries_list))

    # stats
    missing_mono = sum(1 for e in entries_list if e.monoisotopic_mass is None)
    missing_formula = sum(1 for e in entries_list if e.formula is None)
    if missing_mono > 0 or missing_formula > 0:
        logger.warning("\n  ⚠️  Data Completeness:")
        if missing_mono > 0:
            logger.warning("      Missing monoisotopic mass: %d", missing_mono)
        if missing_formula > 0:
            logger.warning("      Missing formula: %d", missing_formula)

    logger.info("\n  📝 Writing to: %s", output_file)

    entries: list[str] = []
    for mod in entries_list:
        formula_str = f'"{mod.formula}"' if mod.formula is not None else "None"
        if mod.dict_composition is not None:
            composition_str = f"parse_composition({mod.dict_composition})"
        else:
            composition_str = "None"

        entry = f'''        "{mod.id}": XlModInfo(
            id="{mod.id}",
            name="{mod.name}",
            formula={formula_str},
            monoisotopic_mass={mod.monoisotopic_mass},
            average_mass={mod.average_mass},
            dict_composition={mod.dict_composition},
    ),'''
        entries.append(entry)

    entries_str = "\n".join(entries)

    content = f'''"""Auto-generated XLMOD data"""
# DO NOT EDIT - generated by gen_xlmod.py

VERSION = "{version}"

import warnings

from .dclass import XlModInfo

try:
    XLMOD_MODIFICATIONS: dict[str, XlModInfo] = {{
{entries_str}
    }}

    XLMOD_NAME_TO_ID: dict[str, str] = {{
        mod.name: mod.id
        for mod in XLMOD_MODIFICATIONS.values()
    }}
except Exception as e:
    warnings.warn(
        f"Exception in xlmod_data: {{e}}. Using empty dictionaries.",
        UserWarning,
        stacklevel=2
    )
    XLMOD_MODIFICATIONS: dict[str, XlModInfo] = {{}}
    XLMOD_NAME_TO_ID: dict[str, str] = {{}}
'''

    with open(output_file, "w") as f:
        f.write(content)

    logger.info("✅ Successfully generated %s", output_file)
    logger.info("   Total entries: %d", len(entries_list))


if __name__ == "__main__":
    gen_xl()
