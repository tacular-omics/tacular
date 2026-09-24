"""Private helpers shared by the ``*Info`` dataclasses."""

from typing import Any, NoReturn

__all__: list[str] = []


def _round(value: float | None, float_precision: int | None) -> float | None:
    """``value`` rounded to ``float_precision`` places; unchanged if either is ``None``."""
    if value is None or float_precision is None:
        return value
    return round(value, float_precision)


class _ReadOnlyDict[K, V](dict[K, V]):
    """A ``dict`` that refuses mutation: the type of every ``*Info.dict_composition``.

    A ``dict`` subclass rather than :class:`types.MappingProxyType` so that it still
    pickles, deep-copies, goes through :func:`dataclasses.asdict` and ``json.dumps``,
    and compares/reprs like the plain dict it wraps. Mutating it raises ``TypeError``
    (as a ``MappingProxyType`` would): the entry's cached ``composition`` depends on it.
    """

    __slots__ = ()

    def __reduce__(self) -> tuple[type, tuple[dict[K, V]]]:
        """Pickle/copy via the constructor (the default path calls ``__setitem__``)."""
        return (type(self), (dict(self),))

    def _read_only(self, *args: Any, **kwargs: Any) -> NoReturn:
        raise TypeError(f"{type(self).__name__} is read-only: build a new dict (e.g. dict(x) | {{...}}) instead.")

    __setitem__ = _read_only
    __delitem__ = _read_only
    __ior__ = _read_only
    clear = _read_only
    pop = _read_only
    popitem = _read_only
    setdefault = _read_only
    update = _read_only


def _freeze_composition(owner: Any) -> None:
    """Replace ``owner.dict_composition`` (a frozen dataclass field) with a
    :class:`_ReadOnlyDict` copy, unless it already is one or is ``None``.
    Call from ``__post_init__``."""
    composition = owner.dict_composition
    if composition is not None and type(composition) is not _ReadOnlyDict:
        object.__setattr__(owner, "dict_composition", _ReadOnlyDict(composition))
