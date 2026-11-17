"""Chemical formula strings to compositions and masses.

>>> from tacular import formula_mass, parse_formula
>>> {str(element): count for element, count in parse_formula("C6H12O6").items()}
{'C': 6, 'H': 12, 'O': 6}
>>> formula_mass("C6H12O6")
180.06338810418
>>> formula_mass("[13C6]H12O6") > formula_mass("C6H12O6")
True

A formula is element symbols with optional integer counts (``C6H12O6``, ``H2O``).
A count may be negative (``C6H-2``), and a symbol written twice is summed. A specific
isotope is written in the ProForma spelling, inside brackets: ``[13C6]H12O6``. The bare
spelling ``13C6H12O6`` and the UNIMOD spelling ``H(2)C(6)`` are not accepted, so there is
one formula dialect. Any other input raises :class:`~tacular.errors.TacularError`.
"""

from ._datagen._utils import parse_formula_to_dict
from .elements import ElementInfo, parse_composition
from .errors import TacularError

__all__ = ["parse_formula", "formula_mass"]


def parse_formula(formula: str) -> dict[ElementInfo, int]:
    """Parse a formula string into a composition keyed by :class:`~tacular.elements.ElementInfo`.

    The result has the same shape as :func:`~tacular.elements.parse_composition`. Isotopes
    use the ProForma bracket spelling, so ``"[13C6]H12O6"`` gives the ``13C`` entry of
    ``ELEMENT_LOOKUP`` with a count of 6.

    Raises:
        TacularError: if ``formula`` is not a non-empty string, is not written as element
            symbols with optional counts and ``[13C6]`` isotope groups, or names a symbol
            that is not an element or isotope in the data. The message includes ``formula``.
    """
    if not isinstance(formula, str):
        raise TacularError(f"parse_formula expects a formula string such as 'C6H12O6', got {formula!r}.")
    if not formula.strip():
        raise TacularError(f"Cannot parse an empty formula, got {formula!r}.")
    if not formula.isascii():
        raise TacularError(f"Cannot parse formula {formula!r}: it contains a character that is not ASCII.")
    try:
        counts = parse_formula_to_dict(formula)
    except ValueError as exc:
        raise TacularError(
            f"Cannot parse formula {formula!r}: {exc}. Write elements as 'C6H12O6' and "
            f"isotopes in brackets as '[13C6]H12O6'."
        ) from exc
    try:
        return parse_composition(counts)
    except TacularError as exc:
        raise TacularError(f"Cannot parse formula {formula!r}: {exc}") from exc


def formula_mass(formula: str, monoisotopic: bool = True) -> float:
    """Mass in Daltons of a formula string (see :func:`parse_formula` for the spelling).

    Args:
        formula: Formula such as ``"C6H12O6"`` or ``"[13C6]H12O6"``.
        monoisotopic: Monoisotopic mass if true, average mass if false.

    Raises:
        TacularError: as :func:`parse_formula`.
    """
    return sum(info.get_mass(monoisotopic=monoisotopic) * count for info, count in parse_formula(formula).items())
