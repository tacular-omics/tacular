"""The ``AminoAcidInfo`` dataclass: a single amino acid's identity, mass, and elemental composition."""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field

from .._util import _round
from ..elements import ElementInfo
from ..elements.lookup import _CompositionCache

__all__ = ["AminoAcidInfo"]


@dataclass(frozen=True, slots=True)
class AminoAcidInfo(_CompositionCache):
    """One amino acid (or ambiguity code such as ``B``, ``J``, ``X``, ``Z``)."""

    id: str
    """One-letter code, e.g. ``"A"``."""
    name: str
    """Full name, e.g. ``"Alanine"``."""
    three_letter_code: str
    """Three-letter code, e.g. ``"Ala"``."""
    formula: str | None
    """Residue formula (the amino acid minus water), or ``None`` for an ambiguity code."""
    monoisotopic_mass: float | None
    """Monoisotopic residue mass in Da, or ``None`` if undefined."""
    average_mass: float | None
    """Average residue mass in Da, or ``None`` if undefined."""
    dict_composition: Mapping[str, int] | None = field(hash=False)
    """Residue composition as ``{symbol: count}``, or ``None``. Read-only: shared by every caller."""
    is_mass_ambiguous: bool = False
    """True if the code stands for residues of different masses (``B``, ``Z``, ``X``)."""
    is_ambiguous: bool = False
    """True for an ambiguity code (``B``, ``J``, ``X``, ``Z``); ``J`` (L/I) is not mass-ambiguous."""

    @property
    def composition(self) -> Counter[ElementInfo] | None:
        """The composition keyed by :class:`~tacular.ElementInfo` (a fresh copy on each
        access), or ``None`` if undefined."""
        return self._composition_copy(self.dict_composition) if self.dict_composition is not None else None

    @property
    def one_letter_code(self) -> str:
        """Alias for :attr:`id`, the amino acid's one-letter code (e.g. ``"A"``)."""
        return self.id

    def get_mass(self, *, monoisotopic: bool = True) -> float | None:
        """The monoisotopic mass (default) or average mass; ``None`` if undefined."""
        return self.monoisotopic_mass if monoisotopic else self.average_mass

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Convert to a plain, JSON-serializable dictionary.

        Keys: ``id``, ``name``, ``three_letter_code``, ``formula``,
        ``monoisotopic_mass``, ``average_mass``, ``composition``, ``is_mass_ambiguous``,
        ``is_ambiguous``. ``float_precision`` rounds the masses (default 6); ``None``
        keeps full precision.
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "three_letter_code": self.three_letter_code,
            "formula": self.formula,
            "monoisotopic_mass": _round(self.monoisotopic_mass, float_precision),
            "average_mass": _round(self.average_mass, float_precision),
            "composition": dict(self.dict_composition) if self.dict_composition is not None else None,
            "is_mass_ambiguous": self.is_mass_ambiguous,
            "is_ambiguous": self.is_ambiguous,
        }
