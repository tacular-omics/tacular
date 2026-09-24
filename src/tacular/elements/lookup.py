"""``ELEMENT_LOOKUP``: the periodic-table + isotope lookup every other data type's
mass/composition math is built on.

Accepts flexible keys: a bare symbol (``"C"``, the element with its average mass
and most abundant isotope's mass), an isotope string (``"13C"``, ``"D"``), an
:class:`Element`, or a ``(symbol, mass_number)`` tuple.
"""

from collections import Counter
from collections.abc import Mapping
from functools import cache

from .._lookup import _BaseLookup
from ..errors import TacularKeyError
from .data import ISOTOPES, Element
from .dclass import ElementInfo

__all__ = ["ELEMENT_LOOKUP", "ElementKey", "ElementLookup", "parse_composition"]

type ElementKey = tuple[str | Element, int | None] | str | Element
"""Any key :class:`ElementLookup` accepts."""

_HYDROGEN_ALIASES = {"D": 2, "T": 3}


def _to_element(symbol: str) -> Element:
    try:
        return Element(symbol)
    except ValueError:
        raise TacularKeyError(f"{symbol!r} is not an element symbol.") from None


def _parse_key(key: object) -> tuple[Element, int | None]:
    """Parse any accepted key into ``(Element, mass_number)``; ``mass_number`` is
    ``None`` for the element as a whole.

    Raises:
        TacularKeyError: for a malformed key, an unknown symbol, or an unsupported type.
    """
    if isinstance(key, Element):
        return key, None

    if isinstance(key, tuple):
        if len(key) != 2:
            raise TacularKeyError(f"Element key tuple must be (symbol, mass_number), got {key!r}.")
        symbol, mass_number = key
        if not isinstance(symbol, str) or isinstance(mass_number, bool):
            raise TacularKeyError(f"Element key tuple must be (str, int | None), got {key!r}.")
        if mass_number is not None and not isinstance(mass_number, int):
            raise TacularKeyError(f"Element key tuple must be (str, int | None), got {key!r}.")
    elif isinstance(key, str):
        digits = len(key) - len(key.lstrip("0123456789"))
        symbol = key[digits:]
        if not symbol:
            raise TacularKeyError(f"Element key {key!r} has no element symbol.")
        if key.startswith("0"):
            raise TacularKeyError(f"Element key {key!r} has a leading zero in its mass number.")
        mass_number = int(key[:digits]) if digits else None
    else:
        raise TacularKeyError(f"Element key {key!r} must be a str, Element or (symbol, mass_number) tuple.")

    if symbol in _HYDROGEN_ALIASES:
        implied = _HYDROGEN_ALIASES[symbol]
        if mass_number is not None and mass_number != implied:
            raise TacularKeyError(f"{symbol!r} is hydrogen-{implied}; got mass number {mass_number}.")
        return Element.H, implied
    return _to_element(symbol), mass_number


class ElementLookup(_BaseLookup[ElementKey, tuple[Element, int | None], ElementInfo]):
    """Element and isotope lookup (singleton ``ELEMENT_LOOKUP``).

    Key formats:

    - ``"C"``, ``Element.C`` or ``("C", None)``: carbon as an element (``mass`` is
      the most abundant isotope's, ``average_mass`` the natural average)
    - ``"13C"`` or ``("C", 13)``: carbon-13
    - ``"D"`` / ``"2H"`` and ``"T"`` / ``"3H"``: deuterium and tritium

    Symbols are case-sensitive (``"c"`` does not match). Only isotopes in the bundled
    data resolve. ``lookup[key]`` raises :class:`~tacular.TacularKeyError` for an
    unknown, malformed or wrongly typed key; ``get`` and ``in`` never raise.
    :meth:`keys` are ``(Element, mass_number)`` tuples, ``mass_number`` ``None`` for
    the element entry.
    """

    _kind = "Element"

    def __init__(self, element_data: Mapping[tuple[Element, int | None], ElementInfo]) -> None:
        """Wrap ``element_data``, keyed by ``(Element, mass_number)`` (``None`` for the element)."""
        self._data: dict[tuple[Element, int | None], ElementInfo] = dict(element_data)

    def _entries(self) -> Mapping[tuple[Element, int | None], ElementInfo]:
        return self._data

    def _resolve(self, key: object) -> ElementInfo | None:
        return self._data.get(_parse_key(key))

    def _miss_message(self, key: object) -> str:
        return f"Isotope {key!r} is not in the element data."

    def __repr__(self) -> str:
        """E.g. ``"<ElementLookup: 406 entries, 118 elements>"``."""
        return f"<ElementLookup: {len(self._data)} entries, {len(self.get_elements())} elements>"

    def get_monoisotopic(self, symbol: str | Element) -> ElementInfo:
        """The most abundant isotope of ``symbol`` (e.g. ``"C"`` -> 12C).

        Raises:
            TacularKeyError: if ``symbol`` is not an element with a most abundant isotope.
        """
        for info in self.get_all_isotopes(symbol):
            if info.is_monoisotopic:
                return info
        raise TacularKeyError(f"No most abundant isotope for {symbol!r}.")

    def get_isotope(self, symbol: str | Element, mass_number: int) -> ElementInfo:
        """The isotope ``symbol``-``mass_number`` (e.g. ``("C", 13)``).

        Raises:
            TacularKeyError: if the element or isotope is not in the data.
        """
        if not isinstance(mass_number, int) or isinstance(mass_number, bool):
            raise TacularKeyError(f"mass_number must be an int, got {mass_number!r}.")
        return self[(symbol, mass_number)]

    def get_all_isotopes(self, symbol: str | Element) -> list[ElementInfo]:
        """All isotopes of ``symbol`` (not the element entry), sorted by mass number.

        Raises:
            TacularKeyError: if ``symbol`` is not an element symbol or has no isotopes.
        """
        element = symbol if isinstance(symbol, Element) else _to_element(symbol)
        isotopes = [info for (sym, mn), info in self._data.items() if sym == element and mn is not None]
        if not isotopes:
            raise TacularKeyError(f"No isotopes for element {symbol!r}.")
        return sorted(isotopes, key=lambda info: info.mass_number or 0)

    def get_elements(self) -> list[str]:
        """Sorted unique element symbols in the lookup."""
        return sorted({str(sym) for sym, _ in self._data})

    def get_mass(self, key: ElementKey, *, monoisotopic: bool = True) -> float:
        """Mass of an element or isotope in Da.

        A specific isotope (``"13C"``, ``("C", 13)``) always returns its exact mass;
        ``monoisotopic`` only applies to an element key (``"C"``): the most abundant
        isotope's mass (default) or the natural average mass.

        Raises:
            TacularKeyError: if ``key`` does not resolve.
        """
        info = self[key]
        if info.mass_number is not None:
            return info.mass
        return info.get_mass(monoisotopic=monoisotopic)

    def get_neutron_offsets_and_abundances(self, key: str | Element | ElementInfo) -> list[tuple[int, float]]:
        """All isotopes of the element ``key``, as ``(neutron_offset, abundance)`` pairs.

        ``neutron_offset`` is relative to the most abundant isotope, e.g. ``0`` for
        12C and ``1`` for 13C. Isotopes with no natural abundance report ``0.0``.
        """
        symbol = key.symbol if isinstance(key, ElementInfo) else key
        mono = self.get_monoisotopic(symbol)
        return [(iso.neutron_count - mono.neutron_count, iso.abundance or 0.0) for iso in self.get_all_isotopes(symbol)]

    def get_masses_and_abundances(self, key: str | Element | ElementInfo) -> list[tuple[float, float]]:
        """All isotopes of the element ``key``, as ``(mass, abundance)`` pairs
        (``0.0`` abundance for isotopes with no natural abundance)."""
        symbol = key.symbol if isinstance(key, ElementInfo) else key
        return [(iso.mass, iso.abundance or 0.0) for iso in self.get_all_isotopes(symbol)]


ELEMENT_LOOKUP = ElementLookup(ISOTOPES)


def parse_composition(comp_dict: Mapping[str, int]) -> dict[ElementInfo, int]:
    """Resolve a composition keyed by strings (``{"C": 2, "13C": 1}``) to one keyed by
    :class:`ElementInfo`.

    Raises:
        TacularKeyError: if a key is not an element or isotope in the data.
    """
    return {ELEMENT_LOOKUP[elem_key]: count for elem_key, count in comp_dict.items()}


@cache
def _cached_composition(items: tuple[tuple[str, int], ...]) -> Counter[ElementInfo]:
    """Resolved composition for ``items`` (sorted ``(symbol, count)`` pairs), cached
    module-wide so frozen ``*Info`` dataclasses need no cache field. Callers must copy."""
    return Counter(parse_composition(dict(items)))


class _CompositionCache:
    """Slotted base for the frozen ``*Info`` dataclasses whose ``composition`` property
    resolves ``dict_composition``: memoizes the resolved mapping on the instance.

    The slot is not a dataclass field (not in ``fields``/``asdict``/``repr``/pickle);
    ``dataclasses.replace`` builds a new instance, so a changed ``dict_composition``
    is resolved afresh. ``dict_composition`` is documented read-only. A class uses
    either :meth:`_composition_copy` or :meth:`_composition_dict_copy`, not both.
    """

    __slots__ = ("_resolved_composition",)
    _resolved_composition: dict[ElementInfo, int]

    def _composition_copy(self, dict_composition: Mapping[str, int]) -> Counter[ElementInfo]:
        """A fresh ``Counter`` of the resolved ``dict_composition`` (keys in sorted
        symbol order, shared module-wide cache underneath); callers may mutate it."""
        try:
            resolved = self._resolved_composition
        except AttributeError:
            resolved = _cached_composition(tuple(sorted(dict_composition.items())))
            object.__setattr__(self, "_resolved_composition", resolved)
        copy: Counter[ElementInfo] = Counter()
        dict.update(copy, resolved)  # plain dict copy; skips Counter.update's per-call checks
        return copy

    def _composition_dict_copy(self, dict_composition: Mapping[str, int]) -> dict[ElementInfo, int]:
        """A fresh ``dict`` of the resolved ``dict_composition``, keys in its order
        (as :func:`parse_composition` returns them); callers may mutate it."""
        try:
            resolved = self._resolved_composition
        except AttributeError:
            resolved = parse_composition(dict_composition)
            object.__setattr__(self, "_resolved_composition", resolved)
        return dict(resolved)
