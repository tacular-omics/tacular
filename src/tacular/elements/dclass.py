"""The ``ElementInfo`` dataclass: a chemical element or one specific isotope of it."""

from dataclasses import dataclass, replace
from typing import Any, Self

from .._util import _round
from ..errors import TacularError

__all__ = ["ElementInfo"]


@dataclass(frozen=True, slots=True)
class ElementInfo:
    """Represents an element or specific isotope with its properties.

    Attributes:
        number: Atomic number (number of protons)
        mass_number: Atomic mass number (protons + neutrons), None for non-specific element
        symbol: Element symbol (e.g., 'C', 'H', 'O')
        mass: Isotopic mass in Daltons
        abundance: Natural abundance as fraction (0.0-1.0); 0.0 for synthetic isotopes,
            None for the whole-element entry (``mass_number`` None)
        average_mass: Average atomic mass for the element
        is_monoisotopic: True if most abundant isotope, False if not, None if element is non-specific
    """

    number: int
    mass_number: int | None
    symbol: str
    mass: float
    abundance: float | None
    average_mass: float
    is_monoisotopic: bool | None

    def __hash__(self) -> int:
        """Hash on ``str(self)`` (e.g. ``"13C"``), matching :meth:`__eq__`'s string comparison."""
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
        """Equal to another ``ElementInfo`` with the same ``(number, mass_number)``,
        or to a string equal to ``str(self)`` (e.g. ``ElementInfo(...) == "13C"``)."""
        if isinstance(other, str):
            return str(self) == other
        if isinstance(other, ElementInfo):
            return (self.number, self.mass_number) == (other.number, other.mass_number)
        return NotImplemented

    def _hill_order_key(self) -> tuple[int, str, int, int]:
        """Generate a sorting key for Hill ordering with isotope priorities"""
        # Hill ordering: C first, H second, then alphabetical
        if self.symbol == "C":
            hill_priority = 0
        elif self.symbol == "H":
            hill_priority = 1
        else:
            hill_priority = 2

        # For same symbol:
        # 1. is_monoisotopic == None comes first
        if self.is_monoisotopic is None:
            mono_priority = 0
        else:
            mono_priority = 1

        # 2. Then sort by neutron count (lowest first)
        # If mass_number is None, treat neutron count as -1 (comes before 0)
        if self.mass_number is None:
            neutron = -1
        else:
            neutron = self.mass_number - self.number

        return (hill_priority, self.symbol, mono_priority, neutron)

    def __lt__(self, other: object) -> bool:
        """Order by Hill convention (C, then H, then alphabetical; ties broken by
        isotope specificity then neutron count), for sorting a composition's elements."""
        if not isinstance(other, ElementInfo):
            return NotImplemented
        return self._hill_order_key() < other._hill_order_key()

    def __le__(self, other: object) -> bool:
        """See :meth:`__lt__`."""
        if not isinstance(other, ElementInfo):
            return NotImplemented
        return self._hill_order_key() <= other._hill_order_key()

    def __gt__(self, other: object) -> bool:
        """See :meth:`__lt__`."""
        if not isinstance(other, ElementInfo):
            return NotImplemented
        return self._hill_order_key() > other._hill_order_key()

    def __ge__(self, other: object) -> bool:
        """See :meth:`__lt__`."""
        if not isinstance(other, ElementInfo):
            return NotImplemented
        return self._hill_order_key() >= other._hill_order_key()

    @property
    def neutron_count(self) -> int:
        """Number of neutrons in this isotope.

        Raises:
            TacularError: for the non-specific element entry (``mass_number`` is ``None``).
        """
        if self.mass_number is None:
            raise TacularError(f"{self.symbol!r} is the element entry (no mass number); it has no neutron count.")
        return self.mass_number - self.number

    @property
    def proton_count(self) -> int:
        """Return the number of protons (same as atomic number)."""
        return self.number

    @property
    def is_radioactive(self) -> bool:
        """Return True if this isotope is radioactive (zero natural abundance)."""
        return self.abundance == 0.0

    def __str__(self) -> str:
        """The isotope symbol tacular uses as a composition key: ``"C"`` for the
        non-specific element, ``"13C"`` for a specific isotope."""
        if self.mass_number is None:
            return f"{self.symbol}"
        return f"{self.mass_number}{self.symbol}"

    def get_mass(self, *, monoisotopic: bool = True) -> float:
        """The isotopic mass (default) or, with ``monoisotopic=False``, the element's
        average mass, in Da."""
        return self.mass if monoisotopic else self.average_mass

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Convert to a plain, JSON-serializable dictionary.

        Keys: ``number``, ``symbol``, ``mass_number``, ``mass``, ``abundance``,
        ``average_mass``, ``is_monoisotopic``. ``float_precision`` rounds the masses
        (default 6); ``None`` keeps full precision.
        """
        return {
            "number": self.number,
            "symbol": self.symbol,
            "mass_number": self.mass_number,
            "mass": _round(self.mass, float_precision),
            "abundance": self.abundance,
            "average_mass": _round(self.average_mass, float_precision),
            "is_monoisotopic": self.is_monoisotopic,
        }

    def __repr__(self) -> str:
        """Eval-ish repr including all fields."""
        return (
            f"ElementInfo(number={self.number}, symbol={self.symbol}, mass_number={self.mass_number}, "
            f"mass={self.mass}, abundance={self.abundance}, average_mass={self.average_mass}, "
            f"is_monoisotopic={self.is_monoisotopic})"
        )

    def update(self, **changes: Any) -> Self:
        """Return a copy with the given fields replaced (``dataclasses.replace``).

        Raises:
            TypeError: for a keyword that is not a field of this class.
        """
        return replace(self, **changes)

    def serialize(self, count: int) -> str:
        """Serialize the ElementInfo to a ProForma formula element compatible string.

        Args:
            count: Number of atoms of this element

        Raises:
            TacularError: if ``count`` is zero.
        """
        if count == 0:
            raise TacularError("Count cannot be zero for serialization")
        if count == 1:
            if self.mass_number is not None:
                return f"[{str(self)}]"
            return str(self)
        else:
            if self.mass_number is not None:
                return f"[{str(self)}{count}]"
            return f"{self.symbol}{count}"
