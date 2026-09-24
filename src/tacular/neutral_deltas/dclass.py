"""The ``NeutralDeltaInfo`` dataclass: a neutral loss/gain (e.g. water, ammonia) with its
formula, mass, composition, and the amino acids it can occur at.
"""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field

from .._util import _round
from ..elements.dclass import ElementInfo
from ..elements.lookup import parse_composition

__all__ = ["NeutralDeltaInfo"]


@dataclass(frozen=True, slots=True)
class NeutralDeltaInfo:
    """A neutral loss or gain. Masses are signed: a loss is negative (``H2O`` is -18.0106)."""

    formula: str
    """Formula of the neutral (unsigned), e.g. ``"H2O"``; also the lookup key."""
    name: str
    """Human-readable name, e.g. ``"Water"``."""
    description: str
    """When the delta occurs."""
    amino_acids: frozenset[str]
    """One-letter codes of the residues it can occur at (empty: any)."""
    monoisotopic_mass: float
    """Signed monoisotopic mass delta in Da."""
    average_mass: float
    """Signed average mass delta in Da."""
    dict_composition: Mapping[str, int] = field(hash=False)
    """Signed composition as ``{symbol: count}``. Read-only."""
    _composition: Counter[ElementInfo] = field(init=False, repr=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_composition", Counter(parse_composition(self.dict_composition)))

    def __hash__(self) -> int:
        """Hash on ``name`` only (``dict_composition`` is a plain ``dict``)."""
        return hash(self.name)

    def get_mass(self, *, monoisotopic: bool = True) -> float:
        """The signed monoisotopic (default) or average mass delta in Da."""
        return self.monoisotopic_mass if monoisotopic else self.average_mass

    @property
    def composition(self) -> Counter[ElementInfo]:
        """The signed composition keyed by :class:`~tacular.ElementInfo` (a fresh copy on each access)."""
        return Counter(self._composition)

    def calculate_loss_sites(self, sequence: str) -> int:
        """Number of residues in ``sequence`` this delta can occur at."""
        return sum(1 for aa in sequence if aa in self.amino_acids)

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Convert to a plain, JSON-serializable dictionary.

        Keys: ``formula``, ``name``, ``description``, ``amino_acids`` (sorted list),
        ``monoisotopic_mass``, ``average_mass``, ``composition``. ``float_precision``
        rounds the masses (default 6); ``None`` keeps full precision.
        """
        return {
            "formula": self.formula,
            "name": self.name,
            "description": self.description,
            "amino_acids": sorted(self.amino_acids),
            "monoisotopic_mass": _round(self.monoisotopic_mass, float_precision),
            "average_mass": _round(self.average_mass, float_precision),
            "composition": dict(self.dict_composition),
        }
