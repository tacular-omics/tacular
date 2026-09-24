"""``RefMolLookup`` (singleton ``REFMOL_LOOKUP``): query reference molecules by id, name,
label type, or molecule type.
"""

from collections.abc import Mapping

from .._lookup import _BaseLookup
from .data import REFMOL_DICT, RefMolID
from .dclass import RefMolInfo

__all__ = ["REFMOL_LOOKUP", "RefMolLookup"]


class RefMolLookup(_BaseLookup[str | RefMolID, str, RefMolInfo]):
    """mzPAF reference molecule lookup (singleton ``REFMOL_LOOKUP``), keyed by
    :class:`RefMolID` or name (case-insensitive), with group queries by label
    type and molecule type.

    ``lookup[key]`` raises :class:`~tacular.TacularKeyError` if nothing matches
    (including keys that are not strings); ``get`` / ``in`` / ``query_*`` never
    raise. :meth:`keys` are the names as plain strings, in data order.
    """

    _kind = "Reference molecule"

    def __init__(self, refmol_data: Mapping[RefMolID, RefMolInfo]) -> None:
        """Build name, label-type and molecule-type indexes from ``refmol_data``."""
        self._data: dict[str, RefMolInfo] = {str(k): v for k, v in refmol_data.items()}
        self._by_name = {info.name.lower(): info for info in self._data.values()}
        self._by_label_type: dict[str, list[RefMolInfo]] = {}
        self._by_molecule_type: dict[str, list[RefMolInfo]] = {}
        for info in self._data.values():
            if info.label_type:
                self._by_label_type.setdefault(info.label_type.lower(), []).append(info)
            if info.molecule_type:
                self._by_molecule_type.setdefault(info.molecule_type.lower(), []).append(info)

    def _entries(self) -> Mapping[str, RefMolInfo]:
        return self._data

    def _resolve(self, key: object) -> RefMolInfo | None:
        return self.query_name(key)  # ty: ignore[invalid-argument-type]

    def query_id(self, refmol_id: RefMolID) -> RefMolInfo | None:
        """By :class:`RefMolID` member (or its string value); ``None`` if nothing matches."""
        return self._data.get(refmol_id) if isinstance(refmol_id, str) else None

    def query_name(self, name: str) -> RefMolInfo | None:
        """By name (e.g. ``"TMT126"``; case-insensitive); ``None`` if nothing matches."""
        return self._by_name.get(name.lower()) if isinstance(name, str) else None

    def query_label_type(self, label_type: str) -> list[RefMolInfo]:
        """All molecules of a label type (e.g. ``"TMT"``; case-insensitive), as a new
        list; empty if nothing matches, including for a non-string key."""
        if not isinstance(label_type, str):
            return []
        return list(self._by_label_type.get(label_type.lower(), ()))

    def query_molecule_type(self, molecule_type: str) -> list[RefMolInfo]:
        """All molecules of a molecule type (e.g. ``"reporter"``; case-insensitive), as
        a new list; empty if nothing matches, including for a non-string key."""
        if not isinstance(molecule_type, str):
            return []
        return list(self._by_molecule_type.get(molecule_type.lower(), ()))


REFMOL_LOOKUP = RefMolLookup(REFMOL_DICT)
