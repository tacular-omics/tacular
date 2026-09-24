"""Tests for tacular.tolerance."""

import doctest
import math
import typing

import pytest
from hypothesis import given
from hypothesis import strategies as st

import tacular
from tacular import TacularError, da_to_ppm, ppm_error, ppm_to_da, tolerance_window, within_tolerance
from tacular import tolerance as tolerance_module

masses = st.floats(min_value=-1e6, max_value=1e6, allow_nan=False).filter(lambda m: abs(m) > 1e-3)
tolerances = st.floats(min_value=0, max_value=1e4, allow_nan=False)
units = st.sampled_from(["da", "ppm"])


def test_exported_from_top_level():
    for name in tolerance_module.__all__:
        assert name in tacular.__all__
        assert getattr(tacular, name) is getattr(tolerance_module, name)


def test_module_doctests():
    failures, tests = doctest.testmod(tolerance_module)
    assert tests > 0 and failures == 0


def test_ppm_error_values():
    assert ppm_error(1000.01, 1000.0) == pytest.approx(10.0)
    assert ppm_error(999.99, 1000.0) == pytest.approx(-10.0)
    assert ppm_error(5.0, 5.0) == 0.0
    # sign follows observed - theoretical, also for negative masses
    assert ppm_error(-18.0, -18.0106) == pytest.approx(0.0106 / 18.0106 * 1e6)


@pytest.mark.parametrize("zero", [0, 0.0, -0.0])
def test_zero_denominator_raises(zero):
    with pytest.raises(TacularError):
        ppm_error(1.0, zero)
    with pytest.raises(TacularError):
        da_to_ppm(1.0, zero)
    assert ppm_to_da(10.0, zero) == 0.0


def test_conversions():
    assert da_to_ppm(0.01, 1000.0) == pytest.approx(10.0)
    assert ppm_to_da(10.0, 1000.0) == pytest.approx(0.01)
    assert da_to_ppm(0.01, -1000.0) == pytest.approx(10.0)
    assert ppm_to_da(10.0, -1000.0) == pytest.approx(0.01)


def test_window_values():
    assert tolerance_window(100.0, 0.5) == (99.5, 100.5)
    assert tolerance_window(100.0, 0.5, tolerance_unit="da") == (99.5, 100.5)
    assert tolerance_window(1000.0, 10, tolerance_unit="ppm") == pytest.approx((999.99, 1000.01))
    assert tolerance_window(-1000.0, 10, tolerance_unit="ppm") == pytest.approx((-1000.01, -999.99))
    lo, hi = tolerance_window(100.0, -1.0)
    assert lo > hi  # negative tolerance: empty window


def test_within_tolerance_values():
    assert within_tolerance(100.4, 100.0, 0.5)
    assert not within_tolerance(100.6, 100.0, 0.5)
    assert within_tolerance(1000.005, 1000.0, 10, tolerance_unit="ppm")
    assert not within_tolerance(1000.02, 1000.0, 10, tolerance_unit="ppm")
    assert within_tolerance(-1000.005, -1000.0, 10, tolerance_unit="ppm")


@pytest.mark.parametrize("unit", ["Da", "PPM", "Ppm", "mda", "", None, "th"])
def test_bad_unit_raises(unit):
    with pytest.raises(TacularError):
        tolerance_window(100.0, 1.0, tolerance_unit=unit)
    with pytest.raises(TacularError):
        within_tolerance(100.0, 100.0, 1.0, tolerance_unit=unit)


def test_options_are_keyword_only():
    with pytest.raises(TypeError):
        tolerance_window(100.0, 1.0, "ppm")  # type: ignore[misc]
    with pytest.raises(TypeError):
        within_tolerance(100.0, 100.0, 1.0, "ppm")  # type: ignore[misc]


@given(masses, masses)
def test_ppm_error_round_trips_through_da(observed, theoretical):
    ppm = ppm_error(observed, theoretical)
    assert ppm_to_da(ppm, theoretical) == pytest.approx(observed - theoretical, rel=1e-9, abs=1e-9)


@given(st.floats(min_value=-1e3, max_value=1e3, allow_nan=False), masses)
def test_da_ppm_round_trip(delta, mz):
    assert ppm_to_da(da_to_ppm(delta, mz), mz) == pytest.approx(delta, rel=1e-9, abs=1e-12)
    assert da_to_ppm(ppm_to_da(delta, mz), mz) == pytest.approx(delta, rel=1e-9, abs=1e-9)


@given(masses, tolerances, units)
def test_window_is_symmetric_and_ordered(mass, tol, unit):
    lo, hi = tolerance_window(mass, tol, tolerance_unit=unit)
    assert lo <= mass <= hi
    assert mass - lo == pytest.approx(hi - mass, rel=1e-9, abs=1e-9)
    expected = tol if unit == "da" else abs(mass) * tol / 1e6
    assert (hi - lo) / 2 == pytest.approx(expected, rel=1e-9, abs=1e-9)


@given(masses, tolerances, units)
def test_negative_mass_window_mirrors_positive(mass, tol, unit):
    lo, hi = tolerance_window(mass, tol, tolerance_unit=unit)
    nlo, nhi = tolerance_window(-mass, tol, tolerance_unit=unit)
    assert (nlo, nhi) == (-hi, -lo)


@given(masses, masses, tolerances, units)
def test_within_tolerance_is_the_window(observed, theoretical, tol, unit):
    lo, hi = tolerance_window(theoretical, tol, tolerance_unit=unit)
    assert within_tolerance(observed, theoretical, tol, tolerance_unit=unit) == (lo <= observed <= hi)
    assert within_tolerance(theoretical, theoretical, tol, tolerance_unit=unit)


def _edge_cases():
    # 4997.130779303885 +/- 0.01 is the review's repro: abs(lo - m) > 0.01 after rounding
    return [(4997.130779303885, 0.01, "da"), (100.0, 0.5, "da"), (1000.0, 10.0, "ppm"), (-523.2847, 5.0, "ppm")]


@pytest.mark.parametrize(("theoretical", "tol", "unit"), _edge_cases())
def test_within_tolerance_edges(theoretical, tol, unit):
    lo, hi = tolerance_window(theoretical, tol, tolerance_unit=unit)
    assert within_tolerance(lo, theoretical, tol, tolerance_unit=unit)
    assert within_tolerance(hi, theoretical, tol, tolerance_unit=unit)
    assert within_tolerance(math.nextafter(lo, math.inf), theoretical, tol, tolerance_unit=unit)
    assert within_tolerance(math.nextafter(hi, -math.inf), theoretical, tol, tolerance_unit=unit)
    assert not within_tolerance(math.nextafter(lo, -math.inf), theoretical, tol, tolerance_unit=unit)
    assert not within_tolerance(math.nextafter(hi, math.inf), theoretical, tol, tolerance_unit=unit)


@given(masses, tolerances, units)
def test_within_tolerance_edges_property(theoretical, tol, unit):
    lo, hi = tolerance_window(theoretical, tol, tolerance_unit=unit)
    assert within_tolerance(lo, theoretical, tol, tolerance_unit=unit)
    assert within_tolerance(hi, theoretical, tol, tolerance_unit=unit)
    assert not within_tolerance(math.nextafter(lo, -math.inf), theoretical, tol, tolerance_unit=unit)
    assert not within_tolerance(math.nextafter(hi, math.inf), theoretical, tol, tolerance_unit=unit)


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf])
def test_non_finite_input_raises(bad):
    with pytest.raises(TacularError):
        tolerance_window(bad, 1.0, tolerance_unit="ppm")
    with pytest.raises(TacularError):
        tolerance_window(100.0, bad)
    for args in ((bad, 100.0, 1.0), (100.0, bad, 1.0), (100.0, 100.0, bad)):
        with pytest.raises(TacularError):
            within_tolerance(*args, tolerance_unit="ppm")


def test_negative_tolerance_matches_nothing():
    assert not within_tolerance(100.0, 100.0, -1.0)


@given(masses, st.floats(min_value=0, max_value=1e3, allow_nan=False))
def test_within_ppm_matches_ppm_error(theoretical, tol):
    observed = theoretical + ppm_to_da(tol / 2, theoretical)
    assert within_tolerance(observed, theoretical, tol, tolerance_unit="ppm")
    assert abs(ppm_error(observed, theoretical)) <= tol * (1 + 1e-6) + 1e-6


def test_shared_types_exported() -> None:
    from tacular.types import Polarity, ToleranceUnit

    assert tacular.Polarity is Polarity and tacular.ToleranceUnit is ToleranceUnit
    assert typing.get_args(Polarity) == ("positive", "negative")
    assert typing.get_args(ToleranceUnit) == ("da", "ppm")
