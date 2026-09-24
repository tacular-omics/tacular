"""``FragmentIonInfo``: mass/composition/properties for a fragment ion type (a, b, c, x, y,
z, ...), plus the ``IonTypeProperty`` flag enum used to classify them.
"""

import typing
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Flag, auto

from .._util import _round
from ..elements import ElementInfo, parse_composition
from ..errors import TacularError

# type checking
if typing.TYPE_CHECKING:
    from .data import IonType

__all__ = ["FragmentIonInfo", "IonTypeProperty"]


class IonTypeProperty(Flag):
    """Flag enum for ion type properties."""

    NONE = 0
    FORWARD = auto()  # a, b, c
    BACKWARD = auto()  # x, y, z
    INTERNAL = auto()  # internal fragments
    INTACT = auto()  # precursor, neutral
    AA_SPECIFIC_FWD = auto()  # d, da, db
    AA_SPECIFIC_BWD = auto()  # v, w, wa, wb


@dataclass(frozen=True, slots=True)
class FragmentIonInfo:
    """A fragment ion type: its mass/composition offset and :class:`IonTypeProperty` flags."""

    id: str
    """ProForma/mzPAF ion id, e.g. ``"b"``, ``"y"``, ``"z."``."""
    name: str
    """Human-readable name, e.g. ``"b-ion"``."""
    formula: str | None
    """Offset formula relative to the summed residues, or ``None``."""
    monoisotopic_mass: float | None
    """Monoisotopic mass offset in Da, or ``None``."""
    average_mass: float | None
    """Average mass offset in Da, or ``None``."""
    dict_composition: Mapping[str, int] | None = field(hash=False)
    """Offset composition as ``{symbol: count}``, or ``None``. Read-only."""
    properties: IonTypeProperty = IonTypeProperty.NONE
    """Classification flags (forward, backward, internal, ...)."""
    _composition: Counter[ElementInfo] | None = field(init=False, repr=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        comp = Counter(parse_composition(self.dict_composition)) if self.dict_composition is not None else None
        object.__setattr__(self, "_composition", comp)

    @property
    def ion_type(self) -> "IonType":
        """Resolve `id` to its :class:`~tacular.ion_types.data.IonType` enum member
        (returned unchanged if `id` is already an `IonType`)."""
        from .data import IonType

        if isinstance(self.id, IonType):
            return self.id
        return IonType(self.id)

    @property
    def is_forward(self) -> bool:
        """Check if ion is a forward ion type (a, b, c)"""
        return bool(self.properties & IonTypeProperty.FORWARD)

    @property
    def is_backward(self) -> bool:
        """Check if ion is a backward ion type (x, y, z)"""
        return bool(self.properties & IonTypeProperty.BACKWARD)

    @property
    def is_internal(self) -> bool:
        """Check if ion is an internal fragment"""
        return bool(self.properties & IonTypeProperty.INTERNAL)

    @property
    def is_intact(self) -> bool:
        """Check if ion is an intact ion (precursor, neutral)"""
        return bool(self.properties & IonTypeProperty.INTACT)

    @property
    def is_aa_specific_forward(self) -> bool:
        """Check if ion is an amino acid-specific forward ion (d, da, db)"""
        return bool(self.properties & IonTypeProperty.AA_SPECIFIC_FWD)

    @property
    def is_aa_specific_backward(self) -> bool:
        """Check if ion is an amino acid-specific backward ion (v, w, wa, wb)"""
        return bool(self.properties & IonTypeProperty.AA_SPECIFIC_BWD)

    def get_mass(self, *, monoisotopic: bool = True) -> float:
        """The monoisotopic (default) or average mass offset in Da.

        Raises:
            TacularError: if that mass is not available for this ion type.
        """
        mass = self.monoisotopic_mass if monoisotopic else self.average_mass
        if mass is None:
            kind = "Monoisotopic" if monoisotopic else "Average"
            raise TacularError(f"{kind} mass is not available for ion type {str(self.id)!r}.")
        return mass

    @property
    def composition(self) -> Counter[ElementInfo]:
        """The composition keyed by :class:`~tacular.ElementInfo` (a fresh copy on each access).

        Raises:
            TacularError: if this ion type has no composition.
        """
        if self._composition is None:
            raise TacularError(f"Composition is not available for ion type {str(self.id)!r}.")
        return Counter(self._composition)

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Convert to a plain, JSON-serializable dictionary.

        Keys: ``id``, ``name``, ``formula``, ``monoisotopic_mass``, ``average_mass``,
        ``composition``. ``float_precision`` rounds the masses (default 6); ``None``
        keeps full precision.
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "formula": self.formula,
            "monoisotopic_mass": _round(self.monoisotopic_mass, float_precision),
            "average_mass": _round(self.average_mass, float_precision),
            "composition": dict(self.dict_composition) if self.dict_composition is not None else None,
        }
