"""Mass tolerance helpers: ppm errors, Da <-> ppm conversion, and tolerance windows.

Units are the lowercase strings ``"da"`` and ``"ppm"``. Anything else raises
:class:`~tacular.errors.TacularError`. A ppm tolerance is relative to ``abs(mass)``, so
windows around negative masses (for example, loss deltas) are well formed and symmetric.

>>> from tacular import ppm_error, tolerance_window, within_tolerance
>>> ppm_error(1000.01, 1000.0)
9.999999999990905
>>> tolerance_window(1000.0, 10, tolerance_unit="ppm")
(999.99, 1000.01)
>>> within_tolerance(1000.005, 1000.0, 10, tolerance_unit="ppm")
True
"""

import math
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
    raise TacularError(f"tolerance_unit must be 'da' or 'ppm', got {unit!r}.")


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

    tacular divides by ``abs(mz)``, so the sign of the result is the sign of ``delta``
    even for a negative ``mz`` (spxtacular's ``da_to_ppm`` divides by the signed ``mz``).

    Raises:
        TacularError: if ``mz`` is 0.
    """
    if mz == 0:
        raise TacularError("mz must be non-zero to convert Da to ppm.")
    return delta / abs(mz) * 1e6


def ppm_to_da(delta_ppm: float, mz: float) -> float:
    """Convert a mass difference ``delta_ppm`` in ppm of ``mz`` to Da: ``delta_ppm * abs(mz) / 1e6``.

    As in :func:`da_to_ppm`, a negative ``mz`` does not flip the sign.
    """
    return delta_ppm * abs(mz) / 1e6


def _require_finite(**values: float) -> None:
    for name, value in values.items():
        if not math.isfinite(value):
            raise TacularError(f"{name} must be finite, got {value!r}.")


def tolerance_window(mass: float, tolerance: float, *, tolerance_unit: ToleranceUnit = "da") -> tuple[float, float]:
    """The ``(lo, hi)`` bounds of a ``tolerance`` window centred on ``mass``.

    ``tolerance_unit="da"`` reads ``tolerance`` in Da; ``tolerance_unit="ppm"`` in ppm of ``abs(mass)``. A
    negative tolerance gives an empty window (``lo > hi``).

    Raises:
        TacularError: if ``tolerance_unit`` is not ``"da"`` or ``"ppm"``, or ``mass`` or
            ``tolerance`` is NaN or infinite.
    """
    _require_finite(mass=mass, tolerance=tolerance)
    width = _half_width(mass, tolerance, tolerance_unit)
    return mass - width, mass + width


def within_tolerance(
    observed: float, theoretical: float, tolerance: float, *, tolerance_unit: ToleranceUnit = "da"
) -> bool:
    """Whether ``observed`` lies in ``tolerance_window(theoretical, tolerance, tolerance_unit=tolerance_unit)``,
    bounds included: ``lo <= observed <= hi``.

    ``tolerance_unit="ppm"`` reads ``tolerance`` in ppm of ``abs(theoretical)``. Testing against the
    window's bounds (not ``abs(observed - theoretical) <= width``) keeps the two functions
    consistent under float rounding: a value exactly at ``lo`` or ``hi`` is within.

    Raises:
        TacularError: if ``tolerance_unit`` is not ``"da"`` or ``"ppm"``, or any number is NaN or
            infinite.
    """
    _require_finite(observed=observed)
    lo, hi = tolerance_window(theoretical, tolerance, tolerance_unit=tolerance_unit)
    return lo <= observed <= hi
