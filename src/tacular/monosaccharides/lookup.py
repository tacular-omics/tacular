"""``MonosaccharideLookup`` (singleton ``MONOSACCHARIDE_LOOKUP``): query monosaccharides
by ProForma name.
"""

from collections.abc import Mapping

from .._lookup import _BaseLookup
from .data import MONOSACCHARIDES, Monosaccharide
from .dclass import MonosaccharideInfo

__all__ = ["MONOSACCHARIDE_LOOKUP", "MonosaccharideLookup"]


class MonosaccharideLookup(_BaseLookup[str | Monosaccharide, str, MonosaccharideInfo]):
    """Monosaccharide lookup (singleton ``MONOSACCHARIDE_LOOKUP``), keyed by
    ProForma name (e.g. ``"Hex"``, ``"HexNAc"``), case-insensitively.

    ``lookup[key]`` raises :class:`~tacular.TacularKeyError` if nothing matches
    (including keys that are not strings); ``get`` / ``in`` / :meth:`query_name`
    never raise. :meth:`keys` are the ProForma names as given (not lowercased).
    """

    _kind = "Monosaccharide"

    def __init__(
        self, monosaccharide_data: Mapping[Monosaccharide, MonosaccharideInfo] | Mapping[str, MonosaccharideInfo]
    ) -> None:
        """Build a case-insensitive ProForma-name index from ``monosaccharide_data``."""
        self._data: dict[str, MonosaccharideInfo] = {str(k): v for k, v in monosaccharide_data.items()}
        self._by_name = {k.lower(): v for k, v in self._data.items()}

    def _entries(self) -> Mapping[str, MonosaccharideInfo]:
        return self._data

    def _resolve(self, key: object) -> MonosaccharideInfo | None:
        return self.query_name(key)  # ty: ignore[invalid-argument-type]

    def query_name(self, name: str) -> MonosaccharideInfo | None:
        """By ProForma name (case-insensitive); ``None`` if nothing matches."""
        return self._by_name.get(name.lower()) if isinstance(name, str) else None


MONOSACCHARIDE_LOOKUP = MonosaccharideLookup(MONOSACCHARIDES)
