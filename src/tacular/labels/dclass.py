"""Dataclasses for quantitative labels: isobaric tags with their reporter ions, and SILAC labels.

Masses are computed from ``dict_composition`` with the bundled element table
(:data:`~tacular.ELEMENT_LOOKUP`), never typed in.
"""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field

from .._util import _round
from ..constants import ELECTRON_MASS
from ..elements import ELEMENT_LOOKUP, ElementInfo
from ..elements.lookup import _CompositionCache

__all__ = ["IsobaricTagInfo", "ReporterIon", "SilacLabelInfo"]


def _composition_mass(dict_composition: Mapping[str, int], *, monoisotopic: bool) -> float:
    return sum(ELEMENT_LOOKUP.get_mass(symbol, monoisotopic=monoisotopic) * n for symbol, n in dict_composition.items())


@dataclass(frozen=True, slots=True)
class ReporterIon(_CompositionCache):
    """One reporter ion channel of an isobaric tag: a singly charged cation."""

    channel: str
    """Channel name, e.g. ``"126"``, ``"127N"``, ``"134C"``, ``"114"``."""
    dict_composition: Mapping[str, int] = field(hash=False)
    """Isotopic composition of the ion, e.g. ``{"C": 7, "13C": 1, "H": 16, "N": 1}`` for
    TMT ``127C`` (C8H16N+). Read-only."""
    mz: float = field(init=False)
    """Exact m/z of the 1+ ion: composition mass minus one electron mass."""

    def __post_init__(self) -> None:
        """Freeze ``dict_composition`` and compute ``mz``."""
        _CompositionCache.__post_init__(self)
        object.__setattr__(self, "mz", _composition_mass(self.dict_composition, monoisotopic=True) - ELECTRON_MASS)

    @property
    def composition(self) -> Counter[ElementInfo]:
        """The composition keyed by :class:`~tacular.ElementInfo` (a fresh copy on each access)."""
        return self._composition_copy(self.dict_composition)

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Plain, JSON-serializable dict: ``channel``, ``mz``, ``composition``."""
        mz = _round(self.mz, float_precision)
        return {"channel": self.channel, "mz": mz, "composition": dict(self.dict_composition)}


@dataclass(frozen=True, slots=True)
class IsobaricTagInfo(_CompositionCache):
    """An isobaric tag reagent set (one plex), e.g. TMT10 or iTRAQ4."""

    name: str
    """Lookup name, e.g. ``"TMT10"``, ``"TMT18"``, ``"iTRAQ8"``."""
    unimod_id: int
    """UNIMOD accession number of the tag modification, e.g. ``737``."""
    unimod_name: str
    """UNIMOD name of the tag modification, e.g. ``"TMT6plex"``."""
    dict_composition: Mapping[str, int] = field(hash=False)
    """Composition of the tag's mass delta, as in UNIMOD. Read-only."""
    reporter_ions: tuple[ReporterIon, ...]
    """Reporter ion channels, in increasing m/z order."""
    aliases: tuple[str, ...] = ()
    """Other accepted lookup names, e.g. ``("TMTpro16",)``."""
    monoisotopic_mass: float = field(init=False)
    """Monoisotopic mass delta in Da, from ``dict_composition``."""
    average_mass: float = field(init=False)
    """Average mass delta in Da, from ``dict_composition``."""

    def __post_init__(self) -> None:
        """Freeze ``dict_composition`` and compute the masses."""
        _CompositionCache.__post_init__(self)
        object.__setattr__(self, "monoisotopic_mass", _composition_mass(self.dict_composition, monoisotopic=True))
        object.__setattr__(self, "average_mass", _composition_mass(self.dict_composition, monoisotopic=False))

    @property
    def plex(self) -> int:
        """Number of reporter channels."""
        return len(self.reporter_ions)

    @property
    def channels(self) -> tuple[str, ...]:
        """Channel names, in increasing m/z order."""
        return tuple(ion.channel for ion in self.reporter_ions)

    @property
    def reporter_mzs(self) -> tuple[float, ...]:
        """Reporter ion m/z values, in channel order."""
        return tuple(ion.mz for ion in self.reporter_ions)

    def reporter(self, channel: str) -> ReporterIon | None:
        """The reporter ion for ``channel`` (e.g. ``"127N"``; case-insensitive), or ``None``."""
        if not isinstance(channel, str):
            return None
        channel = channel.upper()
        return next((ion for ion in self.reporter_ions if ion.channel == channel), None)

    def get_mass(self, *, monoisotopic: bool = True) -> float:
        """The monoisotopic (default) or average mass delta in Da."""
        return self.monoisotopic_mass if monoisotopic else self.average_mass

    @property
    def composition(self) -> Counter[ElementInfo]:
        """The composition keyed by :class:`~tacular.ElementInfo` (a fresh copy on each access)."""
        return self._composition_copy(self.dict_composition)

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Plain, JSON-serializable dict. ``float_precision`` rounds the masses (default 6);
        ``None`` keeps full precision."""
        return {
            "name": self.name,
            "unimod_id": self.unimod_id,
            "unimod_name": self.unimod_name,
            "composition": dict(self.dict_composition),
            "monoisotopic_mass": _round(self.monoisotopic_mass, float_precision),
            "average_mass": _round(self.average_mass, float_precision),
            "reporter_ions": [ion.to_dict(float_precision=float_precision) for ion in self.reporter_ions],
            "aliases": list(self.aliases),
        }


@dataclass(frozen=True, slots=True)
class SilacLabelInfo(_CompositionCache):
    """A SILAC heavy amino acid label, as a mass delta on one residue."""

    name: str
    """Lookup name, e.g. ``"Lys8"``."""
    residue: str
    """One-letter code of the labelled amino acid, ``"K"`` or ``"R"``."""
    unimod_id: int
    """UNIMOD accession number of the label, e.g. ``259``."""
    unimod_name: str
    """UNIMOD name of the label, e.g. ``"Label:13C(6)15N(2)"``."""
    dict_composition: Mapping[str, int] = field(hash=False)
    """Composition of the mass delta, as in UNIMOD, e.g. ``{"C": -6, "13C": 6}``. Read-only."""
    aliases: tuple[str, ...] = ()
    """Other accepted lookup names, e.g. ``("Lys+8", "K+8", "K8")``."""
    monoisotopic_mass: float = field(init=False)
    """Monoisotopic mass delta in Da, from ``dict_composition``."""
    average_mass: float = field(init=False)
    """Average mass delta in Da, from ``dict_composition``."""

    def __post_init__(self) -> None:
        """Freeze ``dict_composition`` and compute the masses."""
        _CompositionCache.__post_init__(self)
        object.__setattr__(self, "monoisotopic_mass", _composition_mass(self.dict_composition, monoisotopic=True))
        object.__setattr__(self, "average_mass", _composition_mass(self.dict_composition, monoisotopic=False))

    def get_mass(self, *, monoisotopic: bool = True) -> float:
        """The monoisotopic (default) or average mass delta in Da."""
        return self.monoisotopic_mass if monoisotopic else self.average_mass

    @property
    def composition(self) -> Counter[ElementInfo]:
        """The composition keyed by :class:`~tacular.ElementInfo` (a fresh copy on each access)."""
        return self._composition_copy(self.dict_composition)

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Plain, JSON-serializable dict. ``float_precision`` rounds the masses (default 6);
        ``None`` keeps full precision."""
        return {
            "name": self.name,
            "residue": self.residue,
            "unimod_id": self.unimod_id,
            "unimod_name": self.unimod_name,
            "composition": dict(self.dict_composition),
            "monoisotopic_mass": _round(self.monoisotopic_mass, float_precision),
            "average_mass": _round(self.average_mass, float_precision),
            "aliases": list(self.aliases),
        }
