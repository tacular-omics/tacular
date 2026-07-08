"""OBO/formula parsing helpers for the data-generation pipeline.

These live in the shipped package (`tacular._datagen._utils`) as the single source
of truth — they are shared by the developer generators here and by the runtime
`tacular update` command. This module simply re-exports them so the generators can
keep importing `from utils import ...`.
"""

from tacular._datagen._utils import (
    calculate_mass,
    format_composition_string,
    get_id_and_name,
    get_obo_metadata,
    is_obsolete,
    parse_formula_to_dict,
    read_obo,
)

__all__ = [
    "calculate_mass",
    "format_composition_string",
    "get_id_and_name",
    "get_obo_metadata",
    "is_obsolete",
    "parse_formula_to_dict",
    "read_obo",
]
