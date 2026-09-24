"""``FragmentIonLookup`` (singleton ``FRAGMENT_ION_LOOKUP``): query fragment ion types by
``IonType``, id, or name.
"""

from collections.abc import Mapping

from .._lookup import _BaseLookup
from .data import ION_TYPE_DICT, IonType
from .dclass import FragmentIonInfo

__all__ = ["FRAGMENT_ION_LOOKUP", "FragmentIonLookup"]


class FragmentIonLookup(_BaseLookup[str | IonType, str, FragmentIonInfo]):
    """Fragment ion type lookup (singleton ``FRAGMENT_ION_LOOKUP``), keyed by
    :class:`IonType`, id (e.g. ``"b"``, ``"y"``) or name, case-insensitively.

    ``lookup[key]`` tries the id, then the name, and raises
    :class:`~tacular.TacularKeyError` if nothing matches (including keys that are not
    strings); ``get`` / ``in`` / ``query_*`` never raise. :meth:`keys` are the ids as
    plain strings, in data order.
    """

    _kind = "Fragment ion"

    def __init__(self, fragment_ion_data: Mapping[IonType, FragmentIonInfo]) -> None:
        """Build id and name indexes from ``fragment_ion_data``."""
        self._data: dict[str, FragmentIonInfo] = {str(ion_id): info for ion_id, info in fragment_ion_data.items()}
        self._by_id = {ion_id.lower(): info for ion_id, info in self._data.items()}
        self._by_name = {info.name.lower(): info for info in self._data.values()}

    def _entries(self) -> Mapping[str, FragmentIonInfo]:
        return self._data

    def _resolve(self, key: object) -> FragmentIonInfo | None:
        return self.query_id(key) or self.query_name(key)  # ty: ignore[invalid-argument-type]

    def _miss_message(self, key: object) -> str:
        return f"Fragment ion {key!r} not found by id or name."

    def query_ion_type(self, ion_type: IonType) -> FragmentIonInfo | None:
        """By :class:`IonType` member; ``None`` if nothing matches."""
        return self.query_id(ion_type)

    def query_id(self, ion_id: str) -> FragmentIonInfo | None:
        """By id (e.g. ``"a"``, ``"y"``, ``"z."``; case-insensitive); ``None`` if nothing matches."""
        return self._by_id.get(ion_id.lower()) if isinstance(ion_id, str) else None

    def query_name(self, name: str) -> FragmentIonInfo | None:
        """By name (e.g. ``"b-ion"``; case-insensitive); ``None`` if nothing matches."""
        return self._by_name.get(name.lower()) if isinstance(name, str) else None


FRAGMENT_ION_LOOKUP = FragmentIonLookup(ION_TYPE_DICT)
