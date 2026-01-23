from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ElementInfo:
    """
    Class to store information about an element isotope
    """

    number: int
    mass_number: int | None
    symbol: str
    mass: float
    abundance: float | None
    average_mass: float
    is_monoisotopic: bool | None

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, other: object) -> bool:
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
        if not isinstance(other, ElementInfo):
            return NotImplemented
        return self._hill_order_key() < other._hill_order_key()

    def __le__(self, other: object) -> bool:
        if not isinstance(other, ElementInfo):
            return NotImplemented
        return self._hill_order_key() <= other._hill_order_key()

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, ElementInfo):
            return NotImplemented
        return self._hill_order_key() > other._hill_order_key()

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, ElementInfo):
            return NotImplemented
        return self._hill_order_key() >= other._hill_order_key()

    @property
    def neutron_count(self) -> int:
        if self.mass_number is None:
            raise ValueError("Mass number is None, cannot calculate neutron count")
        return self.mass_number - self.number

    @property
    def proton_count(self) -> int:
        return self.number

    @property
    def is_radioactive(self) -> bool:
        return self.abundance == 0.0

    def __str__(self) -> str:
        if self.mass_number is None:
            return f"{self.symbol}"
        return f"{self.mass_number}{self.symbol}"

    def get_mass(self, monoisotopic: bool = True) -> float:
        """Get the mass of this element isotope"""
        return self.mass if monoisotopic else self.average_mass

    def to_dict(self, float_precision: int = 6) -> dict[str, object]:
        """Convert the ElementInfo to a dictionary"""
        return {
            "number": self.number,
            "symbol": self.symbol,
            "mass_number": self.mass_number,
            "mass": round(self.mass, float_precision),
            "abundance": self.abundance,
            "average_mass": round(self.average_mass, float_precision),
        }

    def __repr__(self) -> str:
        return (
            f"ElementInfo(number={self.number}, symbol={self.symbol}, mass_number={self.mass_number}, "
            f"mass={self.mass}, abundance={self.abundance}, average_mass={self.average_mass}, "
            f"is_monoisotopic={self.is_monoisotopic})"
        )

    def update(self, **kwargs: object) -> "ElementInfo":
        """Return a new ElementInfo with updated fields"""
        # Since we use slots=True, we need to get fields manually
        current_values: dict[str, object] = {
            "number": self.number,
            "symbol": self.symbol,
            "mass_number": self.mass_number,
            "mass": self.mass,
            "abundance": self.abundance,
            "average_mass": self.average_mass,
            "is_monoisotopic": self.is_monoisotopic,
        }
        return self.__class__(**{**current_values, **kwargs})  # type: ignore

    def serialize(self, count: int) -> str:
        """Serialize the ElementInfo to a string"""
        if count == 0:
            raise ValueError("Count cannot be zero for serialization")
        if count == 1:
            if self.mass_number is not None:
                return f"[{str(self)}]"
            return str(self)
        else:
            if self.mass_number is not None:
                return f"[{str(self)}{count}]"
            return f"{self.symbol}{count}"
