"""``ProteaseLookup`` (singleton ``PROTEASE_LOOKUP``): query proteases by id or name."""

from collections.abc import Iterator

from .data import PROTEASES_DICT, Proteases
from .dclass import ProteaseInfo


class ProteaseLookup:
    """Protease lookup (singleton ``PROTEASE_LOOKUP``), keyed by name or id
    (e.g. ``"trypsin"``, ``"Arg-C"``), case-insensitively.

    ``lookup[key]`` raises ``KeyError`` if nothing matches (including keys that
    are not strings); ``get``/``in`` never raise.
    """

    def __init__(self, data: dict[Proteases, ProteaseInfo]) -> None:
        """Build id/name lookup dicts (keys lowercased) from `data`."""
        self._data: dict[Proteases, ProteaseInfo] = dict(data)
        self.name_to_info: dict[str, ProteaseInfo] = {info.name: info for info in data.values()}

        # make keys lowercase for case-insensitive lookup
        self.id_to_info = {k.lower(): v for k, v in data.items()}
        self.name_to_info = {k.lower(): v for k, v in self.name_to_info.items()}

    def query_id(self, protease_id: str) -> ProteaseInfo | None:
        """Query by protease ID (e.g., 'trypsin', 'arg-c')"""
        if not isinstance(protease_id, str):
            return None
        return self.id_to_info.get(protease_id.lower())

    def query_name(self, name: str) -> ProteaseInfo | None:
        """Query by protease name (e.g., 'Trypsin', 'Arg-C')"""
        if not isinstance(name, str):
            return None
        return self.name_to_info.get(name.lower())

    def __getitem__(self, key: str) -> ProteaseInfo:
        """Get protease by ID or name"""
        # Try name first (more specific)
        info = self.query_name(key)
        if info is not None:
            return info

        # Then try ID
        info = self.query_id(key)
        if info is not None:
            return info

        raise KeyError(f"Protease '{key}' not found by name or ID.")

    def __contains__(self, key: str) -> bool:
        """Check if protease exists"""
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key: str, default: ProteaseInfo | None = None) -> ProteaseInfo | None:
        """Like `lookup[key]`, but return `default` instead of raising `KeyError`."""
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> list[str]:
        """Ids of all proteases (plain strings, e.g. ``"trypsin"``), in data order."""
        return [str(k) for k in self._data]

    def values(self) -> list[ProteaseInfo]:
        """All protease infos, in data order (the same order as iteration)."""
        return list(self.id_to_info.values())

    def __iter__(self) -> Iterator[ProteaseInfo]:
        """Iterator over all ProteaseInfo entries in the lookup."""
        return iter(self.id_to_info.values())

    def __len__(self) -> int:
        """Number of proteases in the lookup."""
        return len(self.id_to_info)


PROTEASE_LOOKUP = ProteaseLookup(PROTEASES_DICT)
