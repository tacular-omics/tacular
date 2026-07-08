"""``MonosaccharideLookup`` (singleton ``MONOSACCHARIDE_LOOKUP``): query monosaccharides
by ProForma name.
"""

from collections.abc import Iterator

from .data import MONOSACCHARIDES, Monosaccharide
from .dclass import MonosaccharideInfo


class MonosaccharideLookup:
    def __init__(self, monosaccharide_data: dict[str, MonosaccharideInfo]) -> None:
        """Build a lowercase ProForma-name-to-info lookup dict from `monosaccharide_data`."""
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

    def get(self, key: str | Monosaccharide) -> MonosaccharideInfo | None:
        """Like `lookup[key]`, but return `None` instead of raising `KeyError`."""
        try:
            return self[key]
        except KeyError:
            return None

    def _query_proforma(self, name: str) -> MonosaccharideInfo | None:
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


monos: dict[str, MonosaccharideInfo] = {str(mono): info for mono, info in MONOSACCHARIDES.items()}

MONOSACCHARIDE_LOOKUP = MonosaccharideLookup(
    monosaccharide_data=monos,
)
