"""Shared OBO-parsing helpers (ported from ``data_gen/generator/utils.py``).

Kept dependency-free apart from tacular's own element lookup so it can run inside
the installed package during ``tacular update``.
"""

from __future__ import annotations

import re
from typing import IO, Any

from ..elements import ELEMENT_LOOKUP


def calculate_mass(composition: dict[str, int], monoisotopic: bool = True) -> float:
    """Calculate mass from an elemental composition (isotope keys like ``13C`` supported)."""
    mass = 0.0
    for element_symbol, count in composition.items():
        element_info = ELEMENT_LOOKUP[element_symbol]
        mass += (element_info.mass if monoisotopic else element_info.average_mass) * count
    return mass


def format_composition_string(composition: dict[str, int]) -> str:
    """Format composition as a Hill-ordered string like ``C2H3NO``."""
    if not composition:
        return ""
    parts: list[str] = []
    elements = list(composition.keys())
    elements.sort(key=lambda el: (0, el) if el == "C" else (1, el) if el == "H" else (2, el))
    for element in elements:
        count = composition[element]
        parts.append(f"{element}{count if count != 1 else ''}")
    return "".join(parts)


def get_obo_metadata(file: IO[str]) -> dict[str, str]:
    """Extract the header metadata (everything before the first stanza) from an OBO file."""
    file.seek(0)
    metadata: dict[str, str] = {}
    for line in file:
        line = line.strip()
        if not line:
            continue
        if line.startswith("["):
            break
        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip()
    file.seek(0)
    return metadata


def read_obo(file: IO[str]) -> list[dict[str, Any]]:
    """Parse an OBO file into a list of ``[Term]`` stanzas (dict of tag -> list[value])."""
    file.seek(0)
    info: dict[str, str] = {}
    elems: list[dict[str, Any]] = []
    skip: bool = False
    d: dict[str, Any] | None = None

    for line in file:
        line = line.rstrip()
        if line == "":
            continue
        if line.startswith("[Typedef]"):
            skip = True
            continue
        if line.startswith("[Term]"):
            skip = False
            if d is not None:
                elems.append(d)
            d = {}
            continue
        if d is None:
            # Header region (before the first [Term]); skip lines without a "key: value".
            if ": " not in line:
                continue
            key, value = line.split(": ", 1)
            info[key] = value
            continue
        if skip:
            continue
        try:
            key, value = line.split(": ", 1)
        except ValueError:
            continue
        d.setdefault(key, []).append(value)

    if d is not None:
        elems.append(d)
    return elems


def get_id_and_name(term: dict[str, Any]) -> tuple[str, str]:
    """Return the single id and name for a term stanza."""
    term_id = term.get("id", [])
    term_name = term.get("name", [])
    if len(term_id) >= 1:
        term_id = term_id[0]
    else:
        raise ValueError("Entry id is None")
    if len(term_name) >= 1:
        term_name = term_name[0]
    else:
        raise ValueError("Entry name is None")
    return term_id, term_name


def is_obsolete(term: dict[str, Any]) -> bool:
    """Whether a term stanza is marked obsolete.

    Lenient: any value other than a truthy ``true`` (case-insensitive) is treated as
    not obsolete, so an unexpected value in a future OBO release cannot crash an update.
    """
    value = term.get("is_obsolete", ["false"])[0]
    return value.strip().lower() == "true"


def parse_formula_to_dict(formula: str) -> dict[str, int]:
    """Parse a formula string to ``{symbol: count}``, supporting ``[13C6]`` isotopes and negatives."""
    composition: dict[str, int] = {}
    if not formula:
        return composition

    i = 0
    while i < len(formula):
        if formula[i].isspace():
            i += 1
            continue
        if formula[i] == "[":
            close = formula.find("]", i)
            if close == -1:
                raise ValueError(f"Unclosed bracket at position {i}")
            content = formula[i + 1 : close]
            match = re.match(r"^(\d+)([A-Z][a-z]?)(-?\d*)$", content)
            if not match:
                raise ValueError(f"Invalid isotope format: [{content}]")
            isotope_num, elem, count_str = match.groups()
            count = int(count_str) if count_str and count_str != "-" else (1 if count_str == "" else -1)
            elem_key = f"{isotope_num}{elem}"
            composition[elem_key] = composition.get(elem_key, 0) + count
            i = close + 1
        elif formula[i].isupper():
            elem = formula[i]
            i += 1
            if i < len(formula) and formula[i].islower():
                elem += formula[i]
                i += 1
            count_str = ""
            if i < len(formula) and formula[i] == "-":
                count_str = "-"
                i += 1
            while i < len(formula) and formula[i].isdigit():
                count_str += formula[i]
                i += 1
            count = int(count_str) if count_str and count_str != "-" else (1 if not count_str else -1)
            composition[elem] = composition.get(elem, 0) + count
        else:
            raise ValueError(f"Unexpected character '{formula[i]}' at position {i}")

    return composition
