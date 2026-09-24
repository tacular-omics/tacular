"""Dataclasses for quantitative labels: isobaric tags with their reporter ions, and SILAC labels.

Masses are computed from ``dict_composition`` with the bundled element table
(:data:`~tacular.ELEMENT_LOOKUP`), never typed in.
"""

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field

from .._util import _ReadOnlyDict, _round
from ..constants import ELECTRON_MASS
from ..elements import ELEMENT_LOOKUP, ElementInfo
from ..elements.lookup import _CompositionCache

__all__ = ["IsobaricTagInfo", "ReporterIonInfo", "SilacLabelInfo"]


def _composition_mass(dict_composition: Mapping[str, int], *, monoisotopic: bool) -> float:
    return sum(ELEMENT_LOOKUP.get_mass(symbol, monoisotopic=monoisotopic) * n for symbol, n in dict_composition.items())


@dataclass(frozen=True, slots=True)
class ReporterIonInfo(_CompositionCache):
    """One reporter ion channel of an isobaric tag: a singly charged cation, plus the
    UNIMOD tag modification that this channel's reagent adds to a peptide."""

    channel: str
    """Channel name, e.g. ``"126"``, ``"127N"``, ``"134C"``, ``"114"``."""
    dict_composition: Mapping[str, int] = field(hash=False)
    """Isotopic composition of the ion, e.g. ``{"C": 7, "13C": 1, "H": 16, "N": 1}`` for
    TMT ``127C`` (C8H16N+). Read-only."""
    tag_unimod_id: int
    """UNIMOD accession of this channel's tag. For iTRAQ it differs by channel (4-plex:
    114 is ``532``, 115 is ``533``, 116/117 are ``214``; 8-plex: 115/118/119/121 are
    ``731``, the rest ``730``). For TMT/TMTpro every channel uses the plex's entry,
    as UNIMOD has one entry per plex."""
    tag_unimod_name: str
    """UNIMOD name of this channel's tag, e.g. ``"iTRAQ4plex114"``."""
    tag_dict_composition: Mapping[str, int] = field(hash=False)
    """Composition of this channel's tag mass delta, as in UNIMOD. Read-only."""
    mz: float = field(init=False)
    """m/z of the 1+ ion, computed: composition mass minus one electron mass."""
    tag_monoisotopic_mass: float = field(init=False)
    """Monoisotopic mass delta of this channel's tag in Da, from ``tag_dict_composition``."""

    def __post_init__(self) -> None:
        """Freeze both compositions and compute ``mz`` and ``tag_monoisotopic_mass``."""
        _CompositionCache.__post_init__(self)
        if type(self.tag_dict_composition) is not _ReadOnlyDict:
            object.__setattr__(self, "tag_dict_composition", _ReadOnlyDict(self.tag_dict_composition))
        object.__setattr__(self, "mz", _composition_mass(self.dict_composition, monoisotopic=True) - ELECTRON_MASS)
        tag_mass = _composition_mass(self.tag_dict_composition, monoisotopic=True)
        object.__setattr__(self, "tag_monoisotopic_mass", tag_mass)

    @property
    def composition(self) -> Counter[ElementInfo]:
        """The composition keyed by :class:`~tacular.ElementInfo` (a fresh copy on each access)."""
        return self._composition_copy(self.dict_composition)

    def to_dict(self, *, float_precision: int | None = 6) -> dict[str, object]:
        """Plain, JSON-serializable dict: ``channel``, ``mz``, ``composition`` and the
        channel's tag (``tag_unimod_id``, ``tag_unimod_name``, ``tag_composition``,
        ``tag_monoisotopic_mass``)."""
        return {
            "channel": self.channel,
            "mz": _round(self.mz, float_precision),
            "composition": dict(self.dict_composition),
            "tag_unimod_id": self.tag_unimod_id,
            "tag_unimod_name": self.tag_unimod_name,
            "tag_composition": dict(self.tag_dict_composition),
            "tag_monoisotopic_mass": _round(self.tag_monoisotopic_mass, float_precision),
        }


@dataclass(frozen=True, slots=True)
class IsobaricTagInfo(_CompositionCache):
    """An isobaric tag reagent set (one plex), e.g. TMT10 or iTRAQ4."""

    name: str
    """Lookup name, e.g. ``"TMT10"``, ``"TMT18"``, ``"iTRAQ8"``."""
    unimod_id: int
    """UNIMOD accession number of the tag modification, e.g. ``737``. This is the
    plex-level entry that search engines set as the tag (for iTRAQ, ``214`` or ``730``);
    per-channel iTRAQ entries are on each :class:`ReporterIonInfo`."""
    unimod_name: str
    """UNIMOD name of the tag modification, e.g. ``"TMT6plex"``."""
    dict_composition: Mapping[str, int] = field(hash=False)
    """Composition of the tag's mass delta, as in UNIMOD. Read-only."""
    reporter_ions: tuple[ReporterIonInfo, ...]
    """Reporter ion channels, in increasing m/z order."""
    aliases: tuple[str, ...] = ()
    """Other accepted lookup names, e.g. ``("TMTpro16",)``."""
    monoisotopic_mass: float = field(init=False)
    """Monoisotopic mass delta in Da, from ``dict_composition``."""
    average_mass: float = field(init=False)
    """Average mass delta in Da, from ``dict_composition`` and the bundled element table.
    UNIMOD uses the same standard atomic weights rounded to 4 decimals (C 12.0107), so its
    average masses differ by up to 6e-4 Da."""

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

    def query_reporter(self, channel: str) -> ReporterIonInfo | None:
        """The reporter ion for ``channel`` (e.g. ``"127N"``; case-insensitive, surrounding
        whitespace ignored), or ``None``."""
        if not isinstance(channel, str):
            return None
        channel = channel.strip().upper()
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
    """Average mass delta in Da, from ``dict_composition`` and the bundled element table
    (UNIMOD rounds the same atomic weights to 4 decimals, so its average may differ by up to 6e-4 Da)."""

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
