"""``ProteaseLookup`` (singleton ``PROTEASE_LOOKUP``): query proteases by id or name."""

from collections.abc import Mapping

from .._lookup import _BaseLookup
from .data import PROTEASE_DICT, Protease
from .dclass import ProteaseInfo

__all__ = ["PROTEASE_LOOKUP", "ProteaseLookup"]


class ProteaseLookup(_BaseLookup[str | Protease, str, ProteaseInfo]):
    """Protease lookup (singleton ``PROTEASE_LOOKUP``), keyed by name or id
    (e.g. ``"trypsin"``, ``"Arg-C"``), case-insensitively.

    ``lookup[key]`` tries the name, then the id, and raises
    :class:`~tacular.TacularKeyError` if nothing matches (including keys that are not
    strings); ``get`` / ``in`` / ``query_*`` never raise. :meth:`keys` are the ids as
    plain strings, in data order.
    """

    _kind = "Protease"

    def __init__(self, data: Mapping[Protease, ProteaseInfo]) -> None:
        """Build id and name indexes (case-insensitive) from ``data``."""
        self._data: dict[str, ProteaseInfo] = {str(k): v for k, v in data.items()}
        self._by_id = {k.lower(): v for k, v in self._data.items()}
        self._by_name = {v.name.lower(): v for v in self._data.values()}

    def _entries(self) -> Mapping[str, ProteaseInfo]:
        return self._data

    def _resolve(self, key: object) -> ProteaseInfo | None:
        return self.query_name(key) or self.query_id(key)  # ty: ignore[invalid-argument-type]

    def _miss_message(self, key: object) -> str:
        return f"Protease {key!r} not found by name or id."

    def query_id(self, protease_id: str) -> ProteaseInfo | None:
        """By id (e.g. ``"trypsin"``, ``"arg_c"``; case-insensitive); ``None`` if nothing matches."""
        return self._by_id.get(protease_id.lower()) if isinstance(protease_id, str) else None

    def query_name(self, name: str) -> ProteaseInfo | None:
        """By name (e.g. ``"Trypsin"``, ``"Arg-C"``; case-insensitive); ``None`` if nothing matches."""
        return self._by_name.get(name.lower()) if isinstance(name, str) else None


PROTEASE_LOOKUP = ProteaseLookup(PROTEASE_DICT)
