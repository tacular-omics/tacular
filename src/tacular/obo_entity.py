"""Shared base class and helpers for ontology entries (UNIMOD, PSI-MOD, RESID, XLMOD,
GNOme, amino acids, elements, ...). Every ``*Info`` dataclass in this package
(``UnimodInfo``, ``PsimodInfo``, ``ElementInfo``, ...) subclasses :class:`OboEntity`
and inherits its fields, serialization, and mass/composition helpers.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Self, TypeVar

from .elements import ElementInfo, parse_composition

T = TypeVar("T", bound="OboEntity")


@dataclass(frozen=True, slots=True)
class OboEntity:
    """Base class for OBO file entities.

    Subclasses (one per ontology/data type) add no fields of their own beyond
    what's declared here; they exist to give each ontology's entries a distinct
    type and, where needed, override :attr:`id_tag` for that ontology's id format.
    """

    id: str
    """The entry's id, in whatever format its source ontology uses (e.g. ``"536"``
    for UNIMOD, ``"AA0001"`` for RESID). Use :attr:`id_tag` for a normalized form."""
    name: str
    """The entry's human-readable name, as given by the source ontology."""
    formula: str | None
    """Chemical formula string (e.g. ``"C2H2O"``), or ``None`` if not available."""
    monoisotopic_mass: float | None
    """Monoisotopic mass delta in Da, or ``None`` if not available."""
    average_mass: float | None
    """Average (isotope-abundance-weighted) mass delta in Da, or ``None`` if not available."""
    dict_composition: Mapping[str, int] | None
    """Elemental composition as ``{symbol: count}`` (isotope keys like ``"13C"`` are
    supported), or ``None`` if not available. Use :attr:`composition` for a version
    keyed by :class:`~tacular.ElementInfo` instead of plain strings."""

    def __str__(self) -> str:
        """Return ``"{name} ({formula})"``, e.g. ``"Acetyl (C2H2O)"``."""
        return f"{self.name} ({self.formula})"

    @property
    def composition(self) -> dict[ElementInfo, int] | None:
        """``dict_composition`` with keys resolved to :class:`~tacular.ElementInfo`
        objects instead of plain symbol strings; ``None`` if no composition is set."""
        if self.dict_composition is None:
            return None
        return parse_composition(self.dict_composition)

    def __repr__(self) -> str:
        """Return an eval-ish repr including id, name, formula, masses, and composition."""
        return (
            f"{self.__class__.__name__}(id={self.id}, name={self.name}, formula={self.formula}, "
            f"monoisotopic_mass={self.monoisotopic_mass}, average_mass={self.average_mass}, "
            f"composition={self.dict_composition})"
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Reconstruct an OboEntity from its ``to_dict`` representation.

        The inverse of :meth:`to_dict`; note ``to_dict`` serialises
        ``dict_composition`` under the ``"composition"`` key.
        """
        return cls(
            id=data["id"],
            name=data["name"],
            formula=data.get("formula"),
            monoisotopic_mass=data.get("monoisotopic_mass"),
            average_mass=data.get("average_mass"),
            dict_composition=data.get("composition"),
        )

    def update(self, **kwargs: Any) -> Self:
        """Return a new instance with updated fields"""
        return self.__class__(
            id=kwargs.get("id", self.id),
            name=kwargs.get("name", self.name),
            formula=kwargs.get("formula", self.formula),
            monoisotopic_mass=kwargs.get("monoisotopic_mass", self.monoisotopic_mass),
            average_mass=kwargs.get("average_mass", self.average_mass),
            dict_composition=kwargs.get("dict_composition", self.dict_composition),
        )

    def mass(self, monoisotopic: bool = True) -> float | None:
        """Get the mass of the entity"""
        return self.monoisotopic_mass if monoisotopic else self.average_mass

    def to_dict(self, float_precision: int | None = 6) -> dict[str, object]:
        """Convert the OboEntity to a dictionary.

        ``float_precision`` rounds the masses (default 6, as used for the bundled
        ``jsons/*.json``). Pass ``None`` to preserve full float precision, e.g. when
        round-tripping through the runtime cache so an updated install matches the
        precision of the bundled ``data.py``.
        """

        def _round(value: float | None) -> float | None:
            if value is None or float_precision is None:
                return value
            return round(value, float_precision)

        return {
            "id": self.id,
            "name": self.name,
            "formula": self.formula,
            "monoisotopic_mass": _round(self.monoisotopic_mass),
            "average_mass": _round(self.average_mass),
            "composition": self.dict_composition,
        }

    def __hash__(self) -> int:
        """Hash on ``(id, name)`` only, so equal entries hash equal even if a mass
        field was later updated via :meth:`update`."""
        return hash(
            (
                self.id,
                self.name,
            )
        )

    @property
    def id_tag(self) -> str:
        """``id`` with leading zeros stripped (e.g. ``"00042"`` -> ``"42"``).

        Subclasses whose ids carry a non-numeric prefix (RESID's ``"AA0001"``, for
        example) override this to strip that prefix too.
        """
        return self.id.lstrip("0")


def filter_infos[T: OboEntity](
    infos: list[T],
    has_monoisotopic_mass: bool | None = None,
    has_composition: bool | None = None,
    **criteria: Any,
) -> list[T]:
    """Filter a list of OboEntity or its subclasses based on criteria."""
    filtered: list[T] = []
    for info in infos:
        match = True

        # Check monoisotopic mass requirement
        if has_monoisotopic_mass is not None:
            if has_monoisotopic_mass and info.monoisotopic_mass is None:
                match = False
            elif not has_monoisotopic_mass and info.monoisotopic_mass is not None:
                match = False

        # Check composition requirement
        if match and has_composition is not None:
            if has_composition and info.dict_composition is None:
                match = False
            elif not has_composition and info.dict_composition is not None:
                match = False

        # Check other criteria
        if match:
            for key, value in criteria.items():
                if not hasattr(info, key) or getattr(info, key) != value:
                    match = False
                    break

        if match:
            filtered.append(info)

    return filtered
