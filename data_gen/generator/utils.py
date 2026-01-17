import re
from typing import IO, Any

from elements import ELEMENT_LOOKUP, ElementInfo

"""
from_string
get_dict_composition
"""


def calculate_mass(composition: dict[str, int], monoisotopic: bool = True) -> float:
    """Calculate mass from elemental composition using peptacular's element lookup"""

    mass = 0.0
    for element_symbol, count in composition.items():
        # Use (symbol, None) to get the most abundant/monoisotopic isotope
        element_info = ELEMENT_LOOKUP[element_symbol]
        if monoisotopic:
            mass += element_info.mass * count
        else:
            mass += element_info.average_mass * count

    return mass


def format_composition_string(composition: dict[str, int]) -> str:
    """Format composition as a string like C2H3NO"""
    if not composition:
        return ""

    # Sort by elements using Hill system (C, H, then alphabetical)
    parts: list[str] = []
    elements = list(composition.keys())
    elements.sort(key=lambda el: (0, el) if el == "C" else (1, el) if el == "H" else (2, el))
    for element in elements:
        count = composition[element]
        parts.append(f"{element}{count if count != 1 else ''}")
    return "".join(parts)


def get_obo_metadata(file: IO[str]) -> dict[str, str]:
    """Extract metadata headers from an OBO file."""
    file.seek(0)
    metadata: dict[str, str] = {}

    for line in file:
        line = line.strip()
        if not line:
            continue

        if line.startswith("["):
            # Reached the first term/stanza
            break

        if ":" in line:
            key, val = line.split(":", 1)
            metadata[key.strip()] = val.strip()

    file.seek(0)
    return metadata


def read_obo(file: IO[str]) -> list[dict[str, Any]]:
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
            key, value = line.split(": ", 1)
            info[key] = value
            continue

        if skip:
            continue

        if line:
            try:
                key, value = line.split(": ", 1)
            except ValueError:
                print(f"Warning: could not parse line: {line}")
                continue

            if key not in d:
                d[key] = [value]
            else:
                d[key].append(value)

    if d is not None:
        elems.append(d)

    return elems


def get_id_and_name(term: dict[str, Any]) -> tuple[str, str]:
    term_id = term.get("id", [])
    term_name = term.get("name", [])

    if len(term_id) > 1:
        print(f"Multiple ids for {term_name} {term_id}")
        term_id = term_id[0]
    elif len(term_id) == 1:
        term_id = term_id[0]
    else:
        raise ValueError("Entry name is None")

    if len(term_name) > 1:
        print(f"Multiple names for {term_id} {term_name}")
        term_name = term_name[0]
    elif len(term_name) == 1:
        term_name = term_name[0]
    else:
        raise ValueError("Entry id is None")

    return term_id, term_name


def is_obsolete(term: dict[str, Any]) -> bool:
    is_obsolete = term.get("is_obsolete", ["false"])[0]
    if is_obsolete in ["true", "false"]:
        is_obsolete = bool(is_obsolete == "true")
    else:
        raise ValueError(f"Invalid is_obsolete value: {is_obsolete}")

    return is_obsolete


def calculate_composition_mass(composition: dict[ElementInfo, int], monoisotopic: bool = True) -> float:
    total_mass = 0.0
    for elem, count in composition.items():
        total_mass += elem.mass * count
    return total_mass


def parse_formula_to_dict(formula: str) -> dict[str, int]:
    """
    Parse formula string to {ElementSymbol: count}, supporting isotope notation.

    Supports:
    - Simple formulas: "C2H6O" -> {"C": 2, "H": 6, "O": 1}
    - Isotopes: "[13C2]H6" -> {"13C": 2, "H": 6}
    - Mixed: "C2[13C6]H5" -> {"C": 2, "13C": 6, "H": 5}
    - Negative counts: "C-1H2" -> {"C": -1, "H": 2}

    Examples:
        parse_formula_to_dict("C2H6O") -> {"C": 2, "H": 6, "O": 1}
        parse_formula_to_dict("[13C2]H6") -> {"13C": 2, "H": 6}
        parse_formula_to_dict("C2[13C6]H5") -> {"C": 2, "13C": 6, "H": 5}
        parse_formula_to_dict("[13C][12C2]H2") -> {"13C": 1, "12C": 2, "H": 2}
    """
    composition: dict[str, int] = {}
    if not formula:
        return composition

    i = 0
    while i < len(formula):
        # Skip whitespace
        if formula[i].isspace():
            i += 1
            continue

        # Handle isotope notation: [13C6] or [13C]
        if formula[i] == "[":
            close = formula.find("]", i)
            if close == -1:
                raise ValueError(f"Unclosed bracket at position {i}")

            # Extract content: "13C6" or "13C-1"
            content = formula[i + 1 : close]

            # Parse: isotope_number + element + optional_count
            match = re.match(r"^(\d+)([A-Z][a-z]?)(-?\d*)$", content)
            if not match:
                raise ValueError(f"Invalid isotope format: [{content}]")

            isotope_num, elem, count_str = match.groups()
            if count_str and count_str != "-":
                count = int(count_str)
            else:
                count = 1 if count_str == "" else -1

            # Key is: isotope_number + element (e.g., "13C")
            elem_key = f"{isotope_num}{elem}"
            composition[elem_key] = composition.get(elem_key, 0) + count

            i = close + 1

        # Handle regular element: C2, Ca, H-1
        elif formula[i].isupper():
            # Get element symbol
            elem = formula[i]
            i += 1
            if i < len(formula) and formula[i].islower():
                elem += formula[i]
                i += 1

            # Get optional count (including negative)
            count_str = ""
            if i < len(formula) and formula[i] == "-":
                count_str = "-"
                i += 1
            while i < len(formula) and formula[i].isdigit():
                count_str += formula[i]
                i += 1

            if count_str and count_str != "-":
                count = int(count_str)
            else:
                count = 1 if not count_str else -1

            composition[elem] = composition.get(elem, 0) + count

        else:
            raise ValueError(f"Unexpected character '{formula[i]}' at position {i}")

    return composition
