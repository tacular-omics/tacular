"""``IsobaricTagLookup`` (singleton ``ISOBARIC_TAG_LOOKUP``) and ``SilacLabelLookup``
(singleton ``SILAC_LOOKUP``): query quantitative labels by name, UNIMOD id or residue.
"""

from collections.abc import Mapping

from .._lookup import _BaseLookup
from ..errors import TacularKeyError
from ._data import ISOBARIC_TAGS, SILAC_LABELS, SILAC_SETS
from .dclass import IsobaricTagInfo, SilacLabelInfo

__all__ = ["ISOBARIC_TAG_LOOKUP", "SILAC_LOOKUP", "IsobaricTagLookup", "SilacLabelLookup"]


def _name_index[V: IsobaricTagInfo | SilacLabelInfo](data: Mapping[str, V]) -> dict[str, V]:
    index: dict[str, V] = {}
    for info in data.values():
        for name in (info.name, *info.aliases):
            index[name.lower()] = info
    return index


def _unimod_number(unimod_id: object) -> int | None:
    if isinstance(unimod_id, bool):
        return None
    if isinstance(unimod_id, int):
        return unimod_id
    if not isinstance(unimod_id, str):
        return None
    text = unimod_id.strip()
    for prefix in ("unimod:", "u:"):
        if text.lower().startswith(prefix):
            text = text[len(prefix) :]
            break
    return int(text) if text.isdigit() else None


class IsobaricTagLookup(_BaseLookup[str, str, IsobaricTagInfo]):
    """Isobaric tag lookup (singleton ``ISOBARIC_TAG_LOOKUP``): TMT 0/2/6/10/11,
    TMTpro 16/18 and iTRAQ 4/8, keyed by name or alias (case-insensitive), e.g.
    ``"TMT10"``, ``"TMT10plex"``, ``"TMTpro18"``, ``"iTRAQ4"``.

    ``lookup[key]`` raises :class:`~tacular.TacularKeyError` if nothing matches;
    ``get`` / ``in`` / ``query_*`` never raise. :meth:`keys` are the names.
    """

    _kind = "Isobaric tag"

    def __init__(self, data: Mapping[str, IsobaricTagInfo]) -> None:
        """Build the name/alias index from ``data``."""
        self._data = dict(data)
        self._by_name = _name_index(self._data)

    def _entries(self) -> Mapping[str, IsobaricTagInfo]:
        return self._data

    def _resolve(self, key: object) -> IsobaricTagInfo | None:
        return self.query_name(key)  # ty: ignore[invalid-argument-type]

    def query_name(self, name: str) -> IsobaricTagInfo | None:
        """By name or alias (case-insensitive); ``None`` if nothing matches."""
        return self._by_name.get(name.lower()) if isinstance(name, str) else None

    def query_unimod_id(self, unimod_id: int | str) -> list[IsobaricTagInfo]:
        """Every plex whose tag is this UNIMOD entry (``737``, ``"UNIMOD:737"``, ``"U:737"``),
        as a new list: TMT6, TMT10 and TMT11 share TMT6plex."""
        number = _unimod_number(unimod_id)
        return [info for info in self._data.values() if info.unimod_id == number]


class SilacLabelLookup(_BaseLookup[str, str, SilacLabelInfo]):
    """SILAC label lookup (singleton ``SILAC_LOOKUP``): Lys4, Lys6, Lys8, Arg6 and Arg10,
    keyed by name or alias (case-insensitive), e.g. ``"Lys8"``, ``"K+8"``, ``"R10"``.
    The common light/medium/heavy sets are :meth:`query_set`.

    ``lookup[key]`` raises :class:`~tacular.TacularKeyError` if nothing matches;
    ``get`` / ``in`` / ``query_*`` never raise, except :meth:`get_set`.
    """

    _kind = "SILAC label"

    def __init__(self, data: Mapping[str, SilacLabelInfo], sets: Mapping[str, tuple[SilacLabelInfo, ...]]) -> None:
        """Build the name/alias index from ``data``; ``sets`` maps a set name to its labels."""
        self._data = dict(data)
        self._by_name = _name_index(self._data)
        self._sets = dict(sets)

    def _entries(self) -> Mapping[str, SilacLabelInfo]:
        return self._data

    def _resolve(self, key: object) -> SilacLabelInfo | None:
        return self.query_name(key)  # ty: ignore[invalid-argument-type]

    def query_name(self, name: str) -> SilacLabelInfo | None:
        """By name or alias (case-insensitive); ``None`` if nothing matches."""
        return self._by_name.get(name.lower()) if isinstance(name, str) else None

    def query_residue(self, residue: str) -> list[SilacLabelInfo]:
        """Every label on a residue (``"K"`` or ``"R"``; case-insensitive), as a new list."""
        if not isinstance(residue, str):
            return []
        residue = residue.upper()
        return [info for info in self._data.values() if info.residue == residue]

    def query_unimod_id(self, unimod_id: int | str) -> list[SilacLabelInfo]:
        """Every label that is this UNIMOD entry (``188``, ``"UNIMOD:188"``), as a new
        list: Lys6 and Arg6 share Label:13C(6)."""
        number = _unimod_number(unimod_id)
        return [info for info in self._data.values() if info.unimod_id == number]

    @property
    def set_names(self) -> tuple[str, ...]:
        """Names of the label sets: ``("light", "medium", "heavy")``."""
        return tuple(self._sets)

    def query_set(self, name: str) -> tuple[SilacLabelInfo, ...] | None:
        """The labels of a set (``"light"``, ``"medium"``, ``"heavy"``; case-insensitive),
        or ``None`` if there is no such set. ``"light"`` is the empty tuple."""
        return self._sets.get(name.lower()) if isinstance(name, str) else None

    def get_set(self, name: str) -> tuple[SilacLabelInfo, ...]:
        """Like :meth:`query_set`, but raise if there is no such set.

        Raises:
            TacularKeyError: if ``name`` is not a set name.
        """
        labels = self.query_set(name)
        if labels is None:
            raise TacularKeyError(f"SILAC set {name!r} not found; expected one of {list(self._sets)}.")
        return labels


ISOBARIC_TAG_LOOKUP = IsobaricTagLookup(ISOBARIC_TAGS)
SILAC_LOOKUP = SilacLabelLookup(SILAC_LABELS, SILAC_SETS)
