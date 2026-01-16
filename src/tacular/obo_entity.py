from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from typing import Any, Self, TypeVar

from .elements import ElementInfo, parse_composition

T = TypeVar("T", bound="OboEntity")


class CV(StrEnum):
    """One of the five supported controlled vocabularies"""

    UNIMOD = "UNIMOD"
    PSI_MOD = "MOD"
    RESID = "RESID"
    GNOME = "GNO"
    XL_MOD = "XLMOD"
    CUSTOM = "CUSTOM"
    OBSERVED = "OBSERVED"


@dataclass(frozen=True, slots=True)
class OboEntity:
    """Base class for OBO file entities"""

    id: str
    name: str
    formula: str | None
    monoisotopic_mass: float | None
    average_mass: float | None
    dict_composition: dict[str, int] | None
    cv: CV | None = None

    def __str__(self) -> str:
        return f"{self.name} ({self.formula})"

    @cached_property
    def composition(self) -> dict[ElementInfo, int] | None:
        """Get the composition as a dict of element symbols to counts"""
        return parse_composition(self.dict_composition) if self.dict_composition is not None else None

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.id}, name={self.name}, formula={self.formula}, "
            f"monoisotopic_mass={self.monoisotopic_mass}, average_mass={self.average_mass}, "
            f"composition={self.dict_composition})"
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

    def to_dict(self, float_precision: int = 6) -> dict[str, object]:
        """Convert the OboEntity to a dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "formula": self.formula,
            "monoisotopic_mass": round(self.monoisotopic_mass, float_precision)
            if self.monoisotopic_mass is not None
            else None,
            "average_mass": round(self.average_mass, float_precision) if self.average_mass is not None else None,
            "composition": self.dict_composition,
        }


class ModEntity(OboEntity):
    cv: CV


def filter_infos(
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
