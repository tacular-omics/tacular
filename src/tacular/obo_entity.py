"""Shared base class for ontology entries.

The ontology ``*Info`` dataclasses (``UnimodInfo``, ``PsimodInfo``, ``ResidInfo``,
``XlmodInfo``, ``GnoInfo``, ``UniprotPtmInfo``) and ``MonosaccharideInfo`` subclass
:class:`OboEntity` and inherit its fields, serialization, and mass/composition helpers.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any, Self

from ._util import _round
from .elements import ElementInfo
from .elements.lookup import _CompositionCache

__all__ = ["OboEntity"]


@dataclass(frozen=True, slots=True)
class OboEntity(_CompositionCache):
    """Base class for OBO file entities.

    Subclasses (one per ontology/data type) add no fields of their own beyond
    what's declared here; they exist to give each ontology's entries a distinct
    type and, where needed, override :attr:`id_tag` for that ontology's id format.

    Instances hash on ``(id, name)``. The other base fields are declared with
    ``field(hash=False)`` so that the ``__hash__`` a ``@dataclass(frozen=True)``
    subclass regenerates also covers only ``(id, name)`` (plus any hashable fields
    the subclass adds), instead of trying to hash the ``dict_composition`` dict.
    """

    id: str
    """The entry's id, in whatever format its source ontology uses (e.g. ``"536"``
    for UNIMOD, ``"AA0001"`` for RESID). Use :attr:`id_tag` for a normalized form."""
    name: str
    """The entry's human-readable name, as given by the source ontology."""
    formula: str | None = field(hash=False)
    """Chemical formula string (e.g. ``"C2H2O"``), or ``None`` if not available."""
    monoisotopic_mass: float | None = field(hash=False)
    """Monoisotopic mass delta in Da, or ``None`` if not available."""
    average_mass: float | None = field(hash=False)
    """Average (isotope-abundance-weighted) mass delta in Da, or ``None`` if not available."""
    dict_composition: Mapping[str, int] | None = field(hash=False)
    """Elemental composition as ``{symbol: count}`` (isotope keys like ``"13C"`` are
    supported), or ``None`` if not available. Use :attr:`composition` for a version
    keyed by :class:`~tacular.ElementInfo` instead of plain strings.

    Read-only: stored as a read-only ``dict`` copy of the mapping passed in, so
    mutating it raises ``TypeError``. :meth:`to_dict` returns a plain copy."""

    def __str__(self) -> str:
        """Return ``"{name} ({formula})"``, e.g. ``"Acetyl (C2H2O)"``."""
        return f"{self.name} ({self.formula})"

    @property
    def composition(self) -> dict[ElementInfo, int] | None:
        """``dict_composition`` with keys resolved to :class:`~tacular.ElementInfo`
        objects instead of plain symbol strings (a fresh dict on each access, resolved
        once per entry); ``None`` if no composition is set.

        Raises:
            TacularKeyError: if a key is not an element or isotope in the data.
        """
        if self.dict_composition is None:
            return None
        return self._composition_dict_copy(self.dict_composition)

    def __repr__(self) -> str:
        """Return an eval-ish repr including id, name, formula, masses, and composition."""
        return (
            f"{self.__class__.__name__}(id={self.id}, name={self.name}, formula={self.formula}, "
            f"monoisotopic_mass={self.monoisotopic_mass}, average_mass={self.average_mass}, "
            f"composition={self.dict_composition})"
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Reconstruct an entry from its :meth:`to_dict` representation (the inverse of
        ``to_dict``, which writes :attr:`dict_composition` under ``"composition"``)."""
        return cls(
            id=data["id"],
            name=data["name"],
            formula=data.get("formula"),
            monoisotopic_mass=data.get("monoisotopic_mass"),
            average_mass=data.get("average_mass"),
            dict_composition=data.get("composition"),
        )

    def update(self, **changes: Any) -> Self:
        """Return a copy with the given fields replaced (``dataclasses.replace``).

        Raises:
            TypeError: for a keyword that is not a field of this class.
        """
        return replace(self, **changes)

    def get_mass(self, *, monoisotopic: bool = True) -> float | None:
        """The monoisotopic mass (default) or average mass; ``None`` if not available."""
        return self.monoisotopic_mass if monoisotopic else self.average_mass

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Convert the entry to a plain, JSON-serializable dictionary.

        Keys: ``id``, ``name``, ``formula``, ``monoisotopic_mass``, ``average_mass`` and
        ``composition`` (a copy of :attr:`dict_composition`, or ``None``); subclasses
        append their own fields. ``float_precision`` rounds the masses (default 6, as
        used for the bundled ``jsons/*.json``); ``None`` keeps full precision, e.g. when
        round-tripping through the ``tacular update`` cache.
        """
        return {
            "id": self.id,
            "name": self.name,
            "formula": self.formula,
            "monoisotopic_mass": _round(self.monoisotopic_mass, float_precision),
            "average_mass": _round(self.average_mass, float_precision),
            # A copy: dict_composition is shared with the lookup and must stay read-only.
            "composition": dict(self.dict_composition) if self.dict_composition is not None else None,
        }

    def __hash__(self) -> int:
        """Hash on ``(id, name)`` only, so equal entries hash equal even if a mass
        field was later updated via :meth:`update`."""
        return hash((self.id, self.name))

    @property
    def id_tag(self) -> str:
        """``id`` with leading zeros stripped (e.g. ``"00042"`` -> ``"42"``).

        Subclasses whose ids carry a non-numeric prefix (RESID's ``"AA0001"``, for
        example) override this to strip that prefix too.
        """
        return self.id.lstrip("0")
