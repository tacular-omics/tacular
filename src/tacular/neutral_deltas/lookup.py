"""``NeutralDeltaLookup`` (singleton ``NEUTRAL_DELTA_LOOKUP``): query neutral deltas by
``NeutralDelta`` enum, formula, or name.
"""

from collections.abc import Mapping

from .._lookup import _BaseLookup
from .data import NEUTRAL_DELTA_DICT, NeutralDelta
from .dclass import NeutralDeltaInfo

__all__ = ["NEUTRAL_DELTA_LOOKUP", "NeutralDeltaLookup"]


class NeutralDeltaLookup(_BaseLookup[str | NeutralDelta, str, NeutralDeltaInfo]):
    """Neutral loss/gain lookup (singleton ``NEUTRAL_DELTA_LOOKUP``), keyed by
    :class:`NeutralDelta`, formula (e.g. ``"H2O"``) or name, case-insensitively.

    ``lookup[key]`` tries the formula, then the name, and raises
    :class:`~tacular.TacularKeyError` if nothing matches (including keys that are not
    strings); ``get`` / ``in`` / ``query_*`` never raise. :meth:`keys` are the
    formulas as plain strings, in data order.
    """

    _kind = "Neutral delta"

    def __init__(self, neutral_delta_data: Mapping[NeutralDelta, NeutralDeltaInfo]) -> None:
        """Build formula and name indexes from ``neutral_delta_data``."""
        self._data: dict[str, NeutralDeltaInfo] = {str(k): info for k, info in neutral_delta_data.items()}
        self._by_formula = {info.formula.lower(): info for info in self._data.values()}
        self._by_name = {info.name.lower(): info for info in self._data.values()}

    def _entries(self) -> Mapping[str, NeutralDeltaInfo]:
        return self._data

    def _resolve(self, key: object) -> NeutralDeltaInfo | None:
        return self.query_formula(key) or self.query_name(key)  # ty: ignore[invalid-argument-type]

    def _miss_message(self, key: object) -> str:
        return f"Neutral delta {key!r} not found by formula or name."

    def query_delta(self, delta: NeutralDelta) -> NeutralDeltaInfo | None:
        """By :class:`NeutralDelta` member; ``None`` if nothing matches."""
        return self.query_formula(delta)

    def query_formula(self, formula: str) -> NeutralDeltaInfo | None:
        """By formula (e.g. ``"H2O"``; case-insensitive); ``None`` if nothing matches."""
        return self._by_formula.get(formula.lower()) if isinstance(formula, str) else None

    def query_name(self, name: str) -> NeutralDeltaInfo | None:
        """By name (e.g. ``"Water"``; case-insensitive); ``None`` if nothing matches."""
        return self._by_name.get(name.lower()) if isinstance(name, str) else None


NEUTRAL_DELTA_LOOKUP = NeutralDeltaLookup(NEUTRAL_DELTA_DICT)
