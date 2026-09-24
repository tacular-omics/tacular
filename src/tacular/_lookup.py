"""Private base class giving every ``*_LOOKUP`` singleton the same mapping-style surface.

Subclasses provide :meth:`_BaseLookup._entries` (canonical key -> entry, in
iteration order) and :meth:`_BaseLookup._resolve` (any accepted query -> entry or
``None``); this class derives ``lookup[key]``, ``get``, ``in``, ``len``, iteration,
``keys``, ``values`` and ``items`` from them, with one error policy:
``lookup[key]`` raises :class:`~tacular.TacularKeyError` (a ``KeyError`` and a
``ValueError``) and ``get`` / ``in`` never raise.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator, Mapping

from .errors import TacularKeyError

__all__: list[str] = []


class _BaseLookup[Q, K, V](ABC):
    """Mapping-style lookup: ``Q`` is the accepted query type, ``K`` the canonical
    key type returned by :meth:`keys`, ``V`` the entry type."""

    _kind: str = "Entry"
    """Noun used in error messages, e.g. ``"Amino acid"``."""

    @abstractmethod
    def _entries(self) -> Mapping[K, V]:
        """Canonical key -> entry, in iteration order."""

    @abstractmethod
    def _resolve(self, key: object) -> V | None:
        """The entry ``key`` refers to, or ``None``. May raise :class:`TacularKeyError`
        with a more specific message (e.g. a malformed element key)."""

    def _miss_message(self, key: object) -> str:
        return f"{self._kind} {key!r} not found."

    def __getitem__(self, key: Q) -> V:
        """``lookup[key]``: the entry ``key`` refers to.

        Raises:
            TacularKeyError: if ``key`` matches no entry, is malformed, or is not a
                supported key type. It is a ``KeyError`` and a ``ValueError``.
        """
        info = self._resolve(key)
        if info is None:
            raise TacularKeyError(self._miss_message(key))
        return info

    def get(self, key: Q, default: V | None = None) -> V | None:
        """Like ``lookup[key]``, but return ``default`` instead of raising."""
        try:
            info = self._resolve(key)
        except TacularKeyError:
            return default
        return default if info is None else info

    def __contains__(self, key: object) -> bool:
        """``key in lookup``: whether ``lookup[key]`` would succeed. Never raises."""
        try:
            return self._resolve(key) is not None
        except TacularKeyError:
            return False

    def __iter__(self) -> Iterator[V]:
        """Iterate over the entries (not the keys), in :meth:`keys` order."""
        return iter(self._entries().values())

    def __len__(self) -> int:
        """Number of entries."""
        return len(self._entries())

    def keys(self) -> list[K]:
        """Canonical keys of all entries, in iteration order."""
        return list(self._entries().keys())

    def values(self) -> list[V]:
        """All entries, in iteration order."""
        return list(self._entries().values())

    def items(self) -> list[tuple[K, V]]:
        """``(key, entry)`` pairs, in iteration order."""
        return list(self._entries().items())

    def __repr__(self) -> str:
        """E.g. ``"<AALookup: 26 entries>"``."""
        return f"<{type(self).__name__}: {len(self)} entries>"
