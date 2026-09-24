"""Private helpers shared by the ``*Info`` dataclasses."""

__all__: list[str] = []


def _round(value: float | None, float_precision: int | None) -> float | None:
    """``value`` rounded to ``float_precision`` places; unchanged if either is ``None``."""
    if value is None or float_precision is None:
        return value
    return round(value, float_precision)
