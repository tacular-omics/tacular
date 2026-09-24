"""``MonosaccharideLookup`` (singleton ``MONOSACCHARIDE_LOOKUP``): query monosaccharides
by ProForma name.
"""

from collections.abc import Iterator

from .data import MONOSACCHARIDES, Monosaccharide
from .dclass import MonosaccharideInfo


class MonosaccharideLookup:
    """Monosaccharide lookup (singleton ``MONOSACCHARIDE_LOOKUP``), keyed by
    ProForma name (e.g. ``"Hex"``, ``"HexNAc"``), case-insensitively.

    ``lookup[key]`` raises ``KeyError`` if nothing matches (including keys that
    are not strings); ``get``/``in`` never raise.
    """

    def __init__(self, monosaccharide_data: dict[str, MonosaccharideInfo]) -> None:
        """Build a lowercase ProForma-name-to-info lookup dict from `monosaccharide_data`."""
        self._data: dict[str, MonosaccharideInfo] = dict(monosaccharide_data)
        self.proforma_to_monosaccharide: dict[str, MonosaccharideInfo] = {
            k.lower(): v for k, v in monosaccharide_data.items()
        }

    def __getitem__(self, key: str | Monosaccharide) -> MonosaccharideInfo:
        """`lookup[key]`: query by ProForma name.

        Raises:
            KeyError: if `key` matches no monosaccharide.
        """
        info: MonosaccharideInfo | None = self._query_proforma(key)
        if info is not None:
            return info

        raise KeyError(f"Monosaccharide '{key}' not found.")

    def __contains__(self, key: str) -> bool:
        """`key in lookup`: True if `key` resolves by ProForma name."""
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key: str | Monosaccharide, default: MonosaccharideInfo | None = None) -> MonosaccharideInfo | None:
        """Like `lookup[key]`, but return `default` instead of raising `KeyError`."""
        try:
            return self[key]
        except KeyError:
            return default

    def _query_proforma(self, name: str) -> MonosaccharideInfo | None:
        if not isinstance(name, str):
            return None
        return self.proforma_to_monosaccharide.get(name.lower())

    def proforma(self, name: str) -> MonosaccharideInfo:
        """Look up by ProForma name (case-insensitive).

        Raises:
            KeyError: if `name` matches no monosaccharide.
        """
        val: MonosaccharideInfo | None = self._query_proforma(name)
        if val is None:
            raise KeyError(f"Monosaccharide '{name}' not found by ProForma name.")
        return val

    def __iter__(self) -> Iterator[MonosaccharideInfo]:
        """Iterator over all MonosaccharideInfo entries in the lookup."""
        return iter(self.proforma_to_monosaccharide.values())

    def __len__(self) -> int:
        """Number of monosaccharides in the lookup."""
        return len(self.proforma_to_monosaccharide)

    def keys(self) -> list[str]:
        """ProForma names of all monosaccharides, as given (not lowercased)."""
        return [str(k) for k in self._data]

    def values(self) -> list[MonosaccharideInfo]:
        """All monosaccharide infos (the same order as iteration)."""
        return list(self.proforma_to_monosaccharide.values())


monos: dict[str, MonosaccharideInfo] = {str(mono): info for mono, info in MONOSACCHARIDES.items()}

MONOSACCHARIDE_LOOKUP = MonosaccharideLookup(
    monosaccharide_data=monos,
)
