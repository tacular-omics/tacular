"""``RefMolLookup`` (singleton ``REFMOL_LOOKUP``): query reference molecules by id, name,
label type, or molecule type.
"""

from collections.abc import Iterator

from .data import REFMOL_DICT, RefMolID
from .dclass import RefMolInfo


class RefMolLookup:
    """mzPAF reference molecule lookup (singleton ``REFMOL_LOOKUP``), keyed by
    :class:`RefMolID` or name (case-insensitive), with group queries by label
    type and molecule type.

    ``lookup[key]`` raises ``KeyError`` if nothing matches (including keys that
    are not strings); ``get``/``in`` never raise.
    """

    def __init__(self, refmol_data: dict[RefMolID, RefMolInfo]) -> None:
        """Build id/name/label-type/molecule-type lookup dicts from `refmol_data`."""
        self._refmol_data = refmol_data

        self._refmolid_to_data: dict[RefMolID, RefMolInfo] = {}
        self._name_to_data: dict[str, RefMolInfo] = {}
        self._label_type_to_data: dict[str, list[RefMolInfo]] = {}
        self._molecule_type_to_data: dict[str, list[RefMolInfo]] = {}

        for refmol_id, refmol_info in refmol_data.items():
            self._refmolid_to_data[refmol_id] = refmol_info
            self._name_to_data[refmol_info.name.lower()] = refmol_info

            # Group by label type
            if refmol_info.label_type:
                self._label_type_to_data.setdefault(refmol_info.label_type.lower(), []).append(refmol_info)

            # Group by molecule type
            if refmol_info.molecule_type:
                self._molecule_type_to_data.setdefault(refmol_info.molecule_type.lower(), []).append(refmol_info)

    def query_id(self, refmol_id: RefMolID) -> RefMolInfo | None:
        """Query by RefMolID enum"""
        return self._refmolid_to_data.get(refmol_id)

    def query_name(self, name: str) -> RefMolInfo | None:
        """Query by reference molecule name (e.g., 'TMT126', 'sidechain_A')"""
        if not isinstance(name, str):
            return None
        return self._name_to_data.get(name.lower())

    def query_label_type(self, label_type: str) -> list[RefMolInfo]:
        """Query all molecules by label type (e.g., 'TMT', 'iTRAQ').

        Returns a new list each call; mutating it does not affect the lookup.
        Returns an empty list if nothing matches, including for a non-string key.
        """
        if not isinstance(label_type, str):
            return []
        return list(self._label_type_to_data.get(label_type.lower(), ()))

    def query_molecule_type(self, molecule_type: str) -> list[RefMolInfo]:
        """Query all molecules by molecule type (e.g., 'reporter', 'sidechain', 'nucleobase').

        Returns a new list each call; mutating it does not affect the lookup.
        Returns an empty list if nothing matches, including for a non-string key.
        """
        if not isinstance(molecule_type, str):
            return []
        return list(self._molecule_type_to_data.get(molecule_type.lower(), ()))

    def __getitem__(self, key: str | RefMolID) -> RefMolInfo:
        """Get reference molecule by ID or name"""
        if isinstance(key, RefMolID):
            info = self.query_id(key)
            if info is not None:
                return info
            raise KeyError(f"Reference molecule ID '{key}' not found.")

        # Try name
        info = self.query_name(key)
        if info is not None:
            return info

        raise KeyError(f"Reference molecule '{key}' not found by name.")

    def __contains__(self, key: str | RefMolID) -> bool:
        """Check if reference molecule exists"""
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key: str | RefMolID, default: RefMolInfo | None = None) -> RefMolInfo | None:
        """Like `lookup[key]`, but return `default` instead of raising `KeyError`."""
        try:
            return self[key]
        except KeyError:
            return default

    def __iter__(self) -> Iterator[RefMolInfo]:
        """Iterator over all RefMolInfo entries in the lookup."""
        return iter(self._refmol_data.values())

    def __len__(self) -> int:
        """Number of reference molecules in the lookup."""
        return len(self._refmol_data)

    def keys(self) -> list[str]:
        """Names of all reference molecules (plain strings, e.g. ``"TMT126"``), in data order."""
        return [str(k) for k in self._refmol_data]

    def values(self) -> list[RefMolInfo]:
        """All reference molecule infos, in data order (the same order as iteration)."""
        return list(self._refmol_data.values())


REFMOL_LOOKUP = RefMolLookup(REFMOL_DICT)
