"""Build UniProt PTM ``UniprotPtmInfo`` objects from a ``ptmlist.txt`` flat file.

Ported from ``data_gen/generator/gen_uniprot_ptm.py`` (parsing only; no ``.py``
rendering). ``ptmlist.txt`` is UniProt's own flat-file format (tag-per-line
stanzas terminated by ``//``), not OBO, so this module doesn't share the
``read_obo``/``get_obo_metadata`` helpers in ``_utils.py``, only the formula and
mass helpers. Crosslink entries (``FT   CROSSLNK``) are dropped: their ``TG``/
``PP`` values are compound (e.g. ``"Alanine-Arginine."``) and don't represent a
standalone, single-residue modification.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from ..uniprot_ptm.dclass import UniprotPtmInfo
from ._utils import calculate_mass, format_composition_string, parse_formula_to_dict

DATA_KEY = "uniprot_ptm_modifications"
JSON_NAME = "uniprot_ptm_modifications.json"

_SINGLE_VALUE_TAGS = ("ID", "AC", "FT", "TG", "PA", "PP", "CF", "MM", "MA", "LC")
_MULTI_VALUE_TAGS = ("TR", "KW", "DR")

logger = logging.getLogger(__name__)


def _get_version(lines: list[str]) -> str:
    for line in lines:
        if line.startswith("Release:"):
            return line.split(":", 1)[1].strip()
    return "unknown"


def _stanzas(lines: list[str]) -> Iterator[dict[str, str | list[str]]]:
    """Split ``ptmlist.txt`` lines into per-entry ``{tag: value}`` stanzas."""
    current: dict[str, str | list[str]] = {}
    for raw_line in lines:
        line = raw_line.rstrip("\n")
        if line.startswith("//"):
            if current:
                yield current
            current = {}
            continue
        if len(line) < 2:
            continue

        tag = line[:2]
        value = line[5:].strip() if len(line) > 5 else ""

        if tag in _SINGLE_VALUE_TAGS:
            current[tag] = value
        elif tag in _MULTI_VALUE_TAGS:
            existing = current.get(tag, [])
            current[tag] = [*existing, value]

    if current:
        yield current


def _build_entry(fields: dict[str, str | list[str]]) -> UniprotPtmInfo | None:
    if fields.get("FT") == "CROSSLNK":
        return None

    name = fields.get("ID")
    ac = fields.get("AC")
    if not name or not ac:
        return None

    # Strip "PTM-" prefix, keep zero-padded numeric string e.g. "0450"
    term_id = str(ac).removeprefix("PTM-")

    cf_raw = fields.get("CF")
    formula: str | None = None
    composition: dict[str, int] | None = None
    if cf_raw:
        try:
            composition = parse_formula_to_dict(str(cf_raw))
            formula = format_composition_string(composition)
        except Exception as e:
            logger.warning(
                "[UniProt-PTM] Error parsing formula for %s %s: CF=%r: %s: %s",
                term_id,
                name,
                cf_raw,
                type(e).__name__,
                e,
                exc_info=True,
            )
            formula = None
            composition = None

    mono_mass: float | None = None
    avg_mass: float | None = None
    mm_raw = fields.get("MM")
    ma_raw = fields.get("MA")
    if mm_raw:
        try:
            mono_mass = float(str(mm_raw))
        except ValueError as e:
            logger.warning(
                "[UniProt-PTM] Invalid MM for %s %s: %r: %s: %s",
                term_id,
                name,
                mm_raw,
                type(e).__name__,
                e,
                exc_info=True,
            )
    if ma_raw:
        try:
            avg_mass = float(str(ma_raw))
        except ValueError as e:
            logger.warning(
                "[UniProt-PTM] Invalid MA for %s %s: %r: %s: %s",
                term_id,
                name,
                ma_raw,
                type(e).__name__,
                e,
                exc_info=True,
            )

    # Validate the parsed composition is internally consistent (matches upstream sanity check).
    if composition is not None:
        calculate_mass(composition, monoisotopic=True)
        calculate_mass(composition, monoisotopic=False)

    feature_key = fields.get("FT")
    target = fields.get("TG")
    position_aa = fields.get("PA")
    position_polypeptide = fields.get("PP")
    cellular_location = fields.get("LC")

    return UniprotPtmInfo(
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
        taxonomic_range=tuple(fields.get("TR") or ()),
        keywords=tuple(fields.get("KW") or ()),
        cross_references=tuple(fields.get("DR") or ()),
    )


def build(ptmlist_path: str | Path) -> tuple[str, list[UniprotPtmInfo]]:
    """Parse ``ptmlist_path`` and return ``(version, infos)``."""
    with open(ptmlist_path) as f:
        lines = f.readlines()

    version = _get_version(lines)
    infos = [
        info
        for fields in _stanzas(lines)
        if (info := _build_entry(fields)) is not None
        if not (
            info.formula is None
            and info.monoisotopic_mass is None
            and info.average_mass is None
            and info.dict_composition is None
        )
    ]
    return version, infos
