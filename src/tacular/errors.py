"""Exceptions raised by tacular.

Every error tacular raises for bad input is a :class:`TacularError`, which is a
``ValueError``. A lookup miss (``lookup[key]`` with a key that matches nothing,
including a malformed key or a key of the wrong type) raises
:class:`TacularKeyError`, which is both a ``TacularError`` and a ``KeyError``, so
``except KeyError``, ``except ValueError`` and ``except TacularError`` all catch it.
"""

__all__ = ["TacularError", "TacularKeyError"]


class TacularError(ValueError):
    """Base class for every error tacular raises for bad input or missing data."""


class TacularKeyError(TacularError, KeyError):
    """``lookup[key]`` matched no entry (the key is unknown, malformed, or not a supported type).

    Also a ``KeyError``, so ``lookup.get(key)`` / ``key in lookup`` semantics and
    ``except KeyError`` keep working.
    """

    def __str__(self) -> str:
        # KeyError.__str__ repr()s its argument (adds quotes); keep the plain message.
        return str(self.args[0]) if len(self.args) == 1 else super().__str__()
