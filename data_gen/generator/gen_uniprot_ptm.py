import os
from collections.abc import Generator

from constants import OutputFile
from logging_utils import setup_logger
from utils import calculate_mass, format_composition_string, parse_formula_to_dict

import tacular as pt

logger = setup_logger(__name__, os.path.splitext(os.path.basename(__file__))[0])


def _esc(s: str | None) -> str:
    """Escape a string for inclusion in generated Python source, or return 'None'."""
    if s is None:
        return "None"
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _esc_tuple(t: tuple[str, ...]) -> str:
    """Serialize a tuple of strings for inclusion in generated Python source."""
    if not t:
        return "()"
    items = ", ".join('"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"' for v in t)
    return f"({items},)"


def _parse_ptmlist(lines: list[str]) -> tuple[str, Generator[pt.UniprotPtmInfo, None, None]]:
    """Parse ptmlist.txt lines into (version, generator of UniprotPtmInfo)."""

    version = "unknown"
    for line in lines:
        if line.startswith("Release:"):
            version = line.split(":", 1)[1].strip()
            break

    def _entries() -> Generator[pt.UniprotPtmInfo, None, None]:
        current: dict[str, object] = {}

        for raw_line in lines:
            line = raw_line.rstrip("\n")

            if line.startswith("//"):
                if current:
                    entry = _build_entry(current)

                    if entry is not None:
                        yield entry
                current = {}
                continue

            if len(line) < 2:
                continue

            code = line[:2]
            value = line[5:].strip() if len(line) > 5 else ""

            if code in ("ID", "AC", "FT", "TG", "PA", "PP", "CF", "MM", "MA", "LC"):
                current[code] = value
            elif code in ("TR", "KW", "DR"):
                existing = current.get(code, [])
                current[code] = existing + [value]  # type: ignore[operator]

    return version, _entries()


def _build_entry(fields: dict[str, object]) -> pt.UniprotPtmInfo | None:
    if fields.get("FT") == "CROSSLNK":
        # Skip crosslink entries as they don't represent standalone modifications
        return None

    name = fields.get("ID")
    ac = fields.get("AC")

    if not name or not ac:
        return None

    # Strip "PTM-" prefix, keep zero-padded numeric string e.g. "0450"
    term_id = str(ac).removeprefix("PTM-")

    cf_raw = fields.get("CF")
    mm_raw = fields.get("MM")
    ma_raw = fields.get("MA")

    # Parse correction formula
    formula: str | None = None
    composition: dict[str, int] | None = None

    if cf_raw:
        try:
            composition = parse_formula_to_dict(str(cf_raw))
            formula = format_composition_string(composition)
        except Exception as e:
            logger.warning(
                "[UniProt-PTM] Error parsing formula for %s %s: %s -> %s",
                term_id,
                name,
                cf_raw,
                e,
            )
            formula = None
            composition = None

    # Parse masses
    mono_mass: float | None = None
    avg_mass: float | None = None

    if mm_raw:
        try:
            mono_mass = float(str(mm_raw))
        except ValueError:
            logger.warning("[UniProt-PTM] Invalid MM for %s %s: %s", term_id, name, mm_raw)

    if ma_raw:
        try:
            avg_mass = float(str(ma_raw))
        except ValueError:
            logger.warning("[UniProt-PTM] Invalid MA for %s %s: %s", term_id, name, ma_raw)

    # Validate formula masses against reported masses
    if composition:
        calc_mono = calculate_mass(composition, monoisotopic=True)
        calc_avg = calculate_mass(composition, monoisotopic=False)

        if mono_mass is not None and abs(calc_mono - mono_mass) > 0.01:
            symbol = "🔴" if abs(calc_mono - mono_mass) > 1.0 else "⚠️"
            logger.warning(
                "%s UniProt-PTM MASS MISMATCH [%s]: Monoisotopic calculated=%.6f reported=%.6f Formula=%s",
                symbol,
                term_id,
                calc_mono,
                mono_mass,
                cf_raw,
            )

        if avg_mass is not None and abs(calc_avg - avg_mass) > 0.2:
            symbol = "⚠️⚠️" if abs(calc_avg - avg_mass) > 1.0 else "⚠️"
            logger.warning(
                "%s UniProt-PTM MASS MISMATCH [%s]: Average calculated=%.6f reported=%.6f Formula=%s",
                symbol,
                term_id,
                calc_avg,
                avg_mass,
                cf_raw,
            )

    # Extract new fields
    feature_key = fields.get("FT")
    target = fields.get("TG")
    position_aa = fields.get("PA")
    position_polypeptide = fields.get("PP")
    cellular_location = fields.get("LC")
    taxonomic_range = tuple(fields.get("TR") or [])
    keywords = tuple(fields.get("KW") or [])
    cross_references = tuple(fields.get("DR") or [])

    return pt.UniprotPtmInfo(
        id=term_id,
        name=str(name),
        formula=formula,
        monoisotopic_mass=mono_mass,
        average_mass=avg_mass,
        dict_composition=composition,
        feature_key=str(feature_key) if feature_key is not None else None,
        target=str(target) if target is not None else None,
        position_aa=str(position_aa) if position_aa is not None else None,
        position_polypeptide=str(position_polypeptide) if position_polypeptide is not None else None,
        cellular_location=str(cellular_location) if cellular_location is not None else None,
        taxonomic_range=taxonomic_range,
        keywords=keywords,
        cross_references=cross_references,
    )


def gen_uniprot_ptm(output_file: str = OutputFile.UNIPROT_PTM):
    logger.info("\n" + "=" * 60)
    logger.info("GENERATING UniProt PTM DATA")
    logger.info("=" * 60)

    data_path = "./data/ptmlist.txt"
    logger.info("  📖 Reading from: data_gen/data/ptmlist.txt")

    with open(data_path) as f:
        lines = f.readlines()

    version, entries_gen = _parse_ptmlist(lines)
    logger.info(f"  ℹ️  Version: {version}")

    all_entries = list(entries_gen)
    logger.info(f"  ✓ Parsed {len(all_entries)} UniProt PTM entries")

    missing_mono = sum(1 for m in all_entries if m.monoisotopic_mass is None)
    missing_avg = sum(1 for m in all_entries if m.average_mass is None)
    missing_formula = sum(1 for m in all_entries if m.formula is None)
    if missing_mono or missing_avg or missing_formula:
        logger.warning("\n  ⚠️  Data Completeness:")
        if missing_mono:
            logger.warning(f"      Missing monoisotopic mass: {missing_mono}")
        if missing_avg:
            logger.warning(f"      Missing average mass: {missing_avg}")
        if missing_formula:
            logger.warning(f"      Missing formula: {missing_formula}")

    logger.info(f"\n  📝 Writing to: {output_file}")

    entries: list[str] = []
    for mod in all_entries:
        if (
            mod.formula is None
            and mod.monoisotopic_mass is None
            and mod.average_mass is None
            and mod.dict_composition is None
        ):
            logger.debug(
                "  ⚠️  Skipping UniProt PTM entry with no formula or masses: %s %s",
                mod.id,
                mod.name,
            )
            continue

        formula_str = f'"{mod.formula}"' if mod.formula is not None else "None"
        name_escaped = mod.name.replace("\\", "\\\\").replace('"', '\\"')

        entry = f'''    "{mod.id}": UniprotPtmInfo(
        id="{mod.id}",
        name="{name_escaped}",
        formula={formula_str},
        monoisotopic_mass={mod.monoisotopic_mass},
        average_mass={mod.average_mass},
        dict_composition={mod.dict_composition},
        feature_key={_esc(mod.feature_key)},
        target={_esc(mod.target)},
        position_aa={_esc(mod.position_aa)},
        position_polypeptide={_esc(mod.position_polypeptide)},
        cellular_location={_esc(mod.cellular_location)},
        taxonomic_range={_esc_tuple(mod.taxonomic_range)},
        keywords={_esc_tuple(mod.keywords)},
        cross_references={_esc_tuple(mod.cross_references)},
    ),'''
        entries.append(entry)

    entries_str = "\n".join(entries)

    content = f'''"""Auto-generated UniProt PTM data"""
# DO NOT EDIT - generated by gen_uniprot_ptm.py

import warnings

from .dclass import UniprotPtmInfo

VERSION = "{version}"


try:
    UNIPROT_PTM_MODIFICATIONS: dict[str, UniprotPtmInfo] = {{
{entries_str}
    }}

    UNIPROT_PTM_NAME_TO_ID: dict[str, str] = {{
        mod.name: mod.id
        for mod in UNIPROT_PTM_MODIFICATIONS.values()
    }}
except Exception as e:
    warnings.warn(
        f"Exception in uniprot_ptm data: {{e}}. Using empty dictionaries.",
        UserWarning,
        stacklevel=2,
    )
    UNIPROT_PTM_MODIFICATIONS: dict[str, UniprotPtmInfo] = {{}}
    UNIPROT_PTM_NAME_TO_ID: dict[str, str] = {{}}
'''

    with open(output_file, "w") as f:
        f.write(content)

    logger.info(f"✅ Successfully generated {output_file}")
    logger.info(f"   Total entries written: {len(entries)}")


if __name__ == "__main__":
    gen_uniprot_ptm()
