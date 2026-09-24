"""The ``RefMolInfo`` dataclass: an mzPAF reference molecule (reporter ion, nucleobase, ...)."""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field

from .._util import _round
from ..elements import ElementInfo
from ..elements.lookup import _composition_copy

__all__ = ["RefMolInfo"]


@dataclass(frozen=True, slots=True)
class RefMolInfo:
    """An mzPAF reference molecule."""

    name: str
    """Name and lookup key, e.g. ``"TMT126"``."""
    label_type: str
    """Label family, e.g. ``"TMT"``, ``"iTRAQ"`` (empty if none)."""
    molecule_type: str
    """Kind of molecule, e.g. ``"reporter"``, ``"nucleobase"``."""
    formula: str
    """Chemical formula, e.g. ``"C8H16N+"``."""
    monoisotopic_mass: float
    """Monoisotopic mass in Da, calculated from the formula."""
    average_mass: float
    """Average mass in Da, calculated from the formula."""
    dict_composition: Mapping[str, int] = field(hash=False)
    """Composition as ``{symbol: count}``. Read-only."""

    def get_mass(self, *, monoisotopic: bool = True) -> float:
        """The monoisotopic (default) or average mass in Da."""
        return self.monoisotopic_mass if monoisotopic else self.average_mass

    @property
    def composition(self) -> Counter[ElementInfo]:
        """The composition keyed by :class:`~tacular.ElementInfo` (a fresh copy on each access)."""
        return _composition_copy(self.dict_composition)

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Convert to a plain, JSON-serializable dictionary.

        Keys: ``name``, ``label_type``, ``molecule_type``, ``formula``,
        ``monoisotopic_mass``, ``average_mass``, ``composition``. ``float_precision``
        rounds the masses (default 6); ``None`` keeps full precision.
        """
        return {
            "name": self.name,
            "label_type": self.label_type,
            "molecule_type": self.molecule_type,
            "formula": self.formula,
            "monoisotopic_mass": _round(self.monoisotopic_mass, float_precision),
            "average_mass": _round(self.average_mass, float_precision),
            "composition": dict(self.dict_composition),
        }
