"""Mass tolerance helpers: ppm errors, Da <-> ppm conversion, and tolerance windows.

Units are the lowercase strings ``"da"`` and ``"ppm"``. Anything else raises
:class:`~tacular.errors.TacularError`. A ppm tolerance is relative to ``abs(mass)``, so
windows around negative masses (for example, loss deltas) are well formed and symmetric.

>>> from tacular import ppm_error, tolerance_window, within_tolerance
>>> ppm_error(1000.01, 1000.0)
9.999999999990905
>>> tolerance_window(1000.0, 10, unit="ppm")
(999.99, 1000.01)
>>> within_tolerance(1000.005, 1000.0, 10, unit="ppm")
True
"""

from typing import Literal

from .errors import TacularError

__all__ = [
    "ToleranceUnit",
    "da_to_ppm",
    "ppm_error",
    "ppm_to_da",
    "tolerance_window",
    "within_tolerance",
]

ToleranceUnit = Literal["da", "ppm"]
"""A tolerance unit: ``"da"`` (daltons, absolute) or ``"ppm"`` (parts per million, relative)."""


def _half_width(mass: float, tolerance: float, unit: str) -> float:
    """The half-width in Da of a ``tolerance`` window around ``mass``."""
    if unit == "da":
        return tolerance
    if unit == "ppm":
        return abs(mass) * tolerance / 1e6
    raise TacularError(f"unit must be 'da' or 'ppm', got {unit!r}.")


def ppm_error(observed: float, theoretical: float) -> float:
    """The signed error of ``observed`` in ppm of ``theoretical``:
    ``(observed - theoretical) / abs(theoretical) * 1e6``.

    Raises:
        TacularError: if ``theoretical`` is 0.
    """
    if theoretical == 0:
        raise TacularError("theoretical must be non-zero to compute a ppm error.")
    return (observed - theoretical) / abs(theoretical) * 1e6


def da_to_ppm(delta: float, mz: float) -> float:
    """Convert a mass difference ``delta`` in Da to ppm of ``mz``: ``delta / abs(mz) * 1e6``.

    Raises:
        TacularError: if ``mz`` is 0.
    """
    if mz == 0:
        raise TacularError("mz must be non-zero to convert Da to ppm.")
    return delta / abs(mz) * 1e6


def ppm_to_da(delta_ppm: float, mz: float) -> float:
    """Convert a mass difference ``delta_ppm`` in ppm of ``mz`` to Da: ``delta_ppm * abs(mz) / 1e6``."""
    return delta_ppm * abs(mz) / 1e6


def tolerance_window(mass: float, tolerance: float, *, unit: ToleranceUnit = "da") -> tuple[float, float]:
    """The ``(lo, hi)`` bounds of a ``tolerance`` window centred on ``mass``.

    ``unit="da"`` reads ``tolerance`` in Da; ``unit="ppm"`` in ppm of ``abs(mass)``. A
    negative tolerance gives an empty window (``lo > hi``).

    Raises:
        TacularError: if ``unit`` is not ``"da"`` or ``"ppm"``.
    """
    width = _half_width(mass, tolerance, unit)
    return mass - width, mass + width


def within_tolerance(observed: float, theoretical: float, tolerance: float, *, unit: ToleranceUnit = "da") -> bool:
    """Whether ``abs(observed - theoretical)`` is at most ``tolerance``.

    ``unit="ppm"`` reads ``tolerance`` in ppm of ``abs(theoretical)``. NaN inputs give
    ``False``.

    Raises:
        TacularError: if ``unit`` is not ``"da"`` or ``"ppm"``.
    """
    return abs(observed - theoretical) <= _half_width(theoretical, tolerance, unit)
