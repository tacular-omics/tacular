"""``NeutralDeltaLookup`` (singleton ``NEUTRAL_DELTA_LOOKUP``): query neutral deltas by
``NeutralDelta`` enum, formula, or name.
"""

from collections.abc import Iterator

from .data import NEUTRAL_DELTA_DICT, NeutralDelta
from .dclass import NeutralDeltaInfo


class NeutralDeltaLookup:
    """Neutral loss/gain lookup (singleton ``NEUTRAL_DELTA_LOOKUP``), keyed by
    :class:`NeutralDelta`, formula (e.g. ``"H2O"``) or name, case-insensitively.

    ``lookup[key]`` raises ``KeyError`` if nothing matches (including keys that
    are not strings); ``get``/``in`` never raise.
    """

    def __init__(self, neutral_delta_data: dict[NeutralDelta, NeutralDeltaInfo]) -> None:
        """Build delta/formula/name lookup dicts from `neutral_delta_data`."""
        self._neutral_delta_data = neutral_delta_data

        self._delta_to_data: dict[NeutralDelta, NeutralDeltaInfo] = {}
        self._formula_to_data: dict[str, NeutralDeltaInfo] = {}
        self._name_to_data: dict[str, NeutralDeltaInfo] = {}

        for delta_key, delta_info in neutral_delta_data.items():
            delta_type = NeutralDelta(delta_key)
            self._delta_to_data[delta_type] = delta_info
            self._formula_to_data[delta_info.formula.lower()] = delta_info
            self._name_to_data[delta_info.name.lower()] = delta_info

    def query_delta(self, delta: NeutralDelta) -> NeutralDeltaInfo | None:
        """Query by NeutralDelta enum"""
        return self._delta_to_data.get(delta)

    def query_formula(self, formula: str) -> NeutralDeltaInfo | None:
        """Query by chemical formula (e.g., 'H2O', 'NH3')"""
        if not isinstance(formula, str):
            return None
        return self._formula_to_data.get(formula.lower())

    def query_name(self, name: str) -> NeutralDeltaInfo | None:
        """Query by neutral delta name (e.g., 'Water', 'Ammonia')"""
        if not isinstance(name, str):
            return None
        return self._name_to_data.get(name.lower())

    def __getitem__(self, key: str | NeutralDelta) -> NeutralDeltaInfo:
        """Get neutral delta by formula, name, or NeutralDelta enum"""
        if isinstance(key, NeutralDelta):
            info = self.query_delta(key)
            if info is not None:
                return info
            raise KeyError(f"Neutral delta type '{key}' not found.")

        if not isinstance(key, str):
            raise KeyError(f"Neutral delta {key!r} not found: keys are str or NeutralDelta.")

        # Try formula first
        info = self.query_formula(key)
        if info is not None:
            return info

        # Then try name
        info = self.query_name(key)
        if info is not None:
            return info

        raise KeyError(f"Neutral delta '{key}' not found by formula or name.")

    def __contains__(self, key: str | NeutralDelta) -> bool:
        """Check if neutral delta exists"""
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key: str | NeutralDelta, default: NeutralDeltaInfo | None = None) -> NeutralDeltaInfo | None:
        """Like `lookup[key]`, but return `default` instead of raising `KeyError`."""
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self) -> list[str]:
        """Formulas of all neutral deltas (plain strings, e.g. ``"H2O"``), in data order."""
        return [str(k) for k in self._neutral_delta_data]

    def values(self) -> list[NeutralDeltaInfo]:
        """All neutral delta infos, in data order (the same order as iteration)."""
        return list(self._neutral_delta_data.values())

    def __iter__(self) -> Iterator[NeutralDeltaInfo]:
        """Iterate over all neutral delta infos"""
        return iter(self._neutral_delta_data.values())

    def __len__(self) -> int:
        """Get the number of neutral deltas"""
        return len(self._neutral_delta_data)

    def __repr__(self) -> str:
        """E.g. ``"NeutralDeltaLookup(24 neutral deltas)"``."""
        return f"NeutralDeltaLookup({len(self)} neutral deltas)"


NEUTRAL_DELTA_LOOKUP = NeutralDeltaLookup(NEUTRAL_DELTA_DICT)
