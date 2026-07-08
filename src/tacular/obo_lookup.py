"""Shared lookup base class (:class:`OntologyLookup`) used by every per-ontology
``*_LOOKUP`` singleton in this package (``UNIMOD_LOOKUP``, ``PSIMOD_LOOKUP``, ...).
Handles id/name normalization, query-by-id/name/mass, iteration, and random
sampling; each ontology's ``*Lookup`` subclass just supplies its data, name, and
optional id prefix (see e.g. ``unimod/lookup.py``).
"""

from collections.abc import Iterator
from functools import cached_property
from random import choice

from .obo_entity import OboEntity, filter_infos


def strip_id(key: str, prefix: str | None = None) -> str:
    """Lowercase ``key``, strip a leading ``prefix`` (if present) and leading zeros.

    E.g. ``strip_id("UNIMOD:00042", "unimod:")`` -> ``"42"``.
    """
    key = key.lower()
    if prefix is not None and key.startswith(prefix):
        key = key[len(prefix) :]
    key = key.lstrip("0")
    return key


def convert_key(key: str, prefix: str | None = None) -> int | None:
    """``strip_id`` then parse as ``int``, or ``None`` if the result isn't numeric
    (e.g. RESID's ``"AA0001"`` ids, whose non-numeric suffix can't convert)."""
    try:
        key = strip_id(key, prefix)
        return int(key)
    except ValueError:
        return None


class OntologyLookup[T: OboEntity]:
    """Id/name/mass lookup over a dict of :class:`OboEntity` subclass instances.

    Lookup dictionaries are built lazily on first access (see
    :meth:`_ensure_initialized`), not in ``__init__``, so constructing a lookup
    with cache-resolved data (see :mod:`tacular._cache`) is cheap even before
    any query is made.
    """

    def __init__(
        self,
        data: dict[str, T],
        ontology_name: str,
        _version: str = "",
        _id_prefix: str | None = None,
    ) -> None:
        """
        Args:
            data: Entries keyed by their raw id (e.g. UNIMOD's ``"1"``, ``"536"``, ...).
            ontology_name: Display name used in error messages (e.g. ``"UNIMOD"``).
            _version: Data version string, exposed via :attr:`version`.
            _id_prefix: Prefix to strip from ids/queries before matching (e.g. RESID
                uses ``"aa"`` so ``"AA0001"`` and ``"0001"`` both resolve to the same entry).
        """
        self.ontology_name = ontology_name
        self._version = _version

        # Store raw data, defer processing
        self._raw_data = data
        self.__num_to_info: dict[int, T] | None = None
        self.__id_to_info: dict[str, T] | None = None
        self.__name_to_info: dict[str, T] | None = None
        self._id_prefix = _id_prefix.lower() if _id_prefix is not None else None

    def _ensure_initialized(self) -> None:
        """Lazy initialization of lookup dictionaries."""
        if self.__num_to_info is not None:
            return

        # Build lowercase lookup dicts
        self.__num_to_info = {
            ki: v for k, v in self._raw_data.items() if (ki := convert_key(k, self._id_prefix)) is not None
        }
        self.__id_to_info = {strip_id(k, self._id_prefix): v for k, v in self._raw_data.items()}
        self.__name_to_info = {info.name.lower(): info for info in self._raw_data.values()}

        if len(self.__id_to_info) != len(self._raw_data) != len(self.__name_to_info):
            raise ValueError(
                f"Duplicate or missing IDs found in {self.ontology_name} data. Number of entries: \
             {len(self._raw_data)}, IDs: {len(self.__id_to_info)}, names: {len(self.__name_to_info)}"
            )

    @property
    def _num_to_info(self) -> dict[int, T]:
        """Get the numeric ID to info mapping."""
        self._ensure_initialized()
        if self.__num_to_info is None:
            raise RuntimeError("OntologyLookup not properly initialized.")
        return self.__num_to_info

    @property
    def _id_to_info(self) -> dict[str, T]:
        """Get the ID to info mapping."""
        self._ensure_initialized()
        if self.__id_to_info is None:
            raise RuntimeError("OntologyLookup not properly initialized.")
        return self.__id_to_info

    @property
    def _name_to_info(self) -> dict[str, T]:
        """Get the name to info mapping."""
        self._ensure_initialized()
        if self.__name_to_info is None:
            raise RuntimeError("OntologyLookup not properly initialized.")
        return self.__name_to_info

    @property
    def version(self) -> str:
        """Get the version of the ontology data."""
        return self._version

    def query_id(self, mod_id: str | int) -> T | None:
        """Query by ID, stripping known prefixes."""
        if isinstance(mod_id, int):
            return self._num_to_info.get(mod_id)

        mod_id = strip_id(mod_id, self._id_prefix)
        info = self._id_to_info.get(mod_id)
        if info is not None:
            return info

        # try to convert to int
        try:
            ki = int(mod_id)
        except ValueError:
            ki = None

        if ki is not None:
            return self._num_to_info.get(ki)

        return None

    def query_name(self, name: str) -> T | None:
        """Query by name, stripping known prefixes."""
        return self._name_to_info.get(name.lower())

    def query_mass(self, mass: float, tolerance: float = 0.01, monoisotopic: bool = True) -> list[T]:
        """Query by mass within a given tolerance."""
        matches: list[T] = []
        for info in self._id_to_info.values():
            mod_mass = info.monoisotopic_mass if monoisotopic else info.average_mass
            if mod_mass is not None and abs(mod_mass - mass) <= tolerance:
                matches.append(info)

        return matches

    def __getitem__(self, key: str | int) -> T:
        """``lookup[key]``: query by name first, then by id.

        Raises:
            KeyError: if ``key`` matches no entry by name or id. The message
                names the ontology and the exact key that failed to resolve.
        """
        if isinstance(key, str):
            info = self.query_name(key)
            if info is not None:
                return info

        info = self.query_id(key)
        if info is not None:
            return info

        raise KeyError(f"{self.ontology_name} modification '{key}' not found by name or ID.")

    def __contains__(self, key: str | int) -> bool:
        """``key in lookup``: True if ``key`` resolves by name or id."""
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key: str | int, default: T | None = None) -> T | None:
        """Like ``lookup[key]``, but return ``default`` instead of raising ``KeyError``."""
        try:
            return self[key]
        except KeyError:
            return default

    def __iter__(self) -> Iterator[T]:
        """Iterator over all entries in the lookup."""
        return iter(self._name_to_info.values())

    def values(self) -> list[T]:
        """Get all entries in the lookup."""
        return list(self._name_to_info.values())

    def keys(self) -> list[str]:
        """Get all keys (names) in the lookup."""
        return list(self._name_to_info.keys())

    @cached_property
    def _all_infos_tuple(self) -> tuple[T, ...]:
        """Cached tuple of all entries."""
        return tuple(self._name_to_info.values())

    @cached_property
    def _infos_with_mass_tuple(self) -> tuple[T, ...]:
        """Cached tuple of entries with monoisotopic mass."""
        return tuple(filter_infos(list(self._name_to_info.values()), has_monoisotopic_mass=True))

    @cached_property
    def _infos_with_composition_tuple(self) -> tuple[T, ...]:
        """Cached tuple of entries with composition."""
        return tuple(filter_infos(list(self._name_to_info.values()), has_composition=True))

    @cached_property
    def _infos_with_mass_and_composition_tuple(self) -> tuple[T, ...]:
        """Cached tuple of entries with both mass and composition."""
        return tuple(
            filter_infos(
                list(self._name_to_info.values()),
                has_monoisotopic_mass=True,
                has_composition=True,
            )
        )

    def choice(self, require_monoisotopic_mass: bool = True, require_composition: bool = True) -> T:
        """Get a random entry from the lookup."""
        if require_monoisotopic_mass and require_composition:
            valid_infos = self._infos_with_mass_and_composition_tuple
        elif require_monoisotopic_mass:
            valid_infos = self._infos_with_mass_tuple
        elif require_composition:
            valid_infos = self._infos_with_composition_tuple
        else:
            valid_infos = self._all_infos_tuple

        if not valid_infos:
            raise ValueError(f"No valid {self.ontology_name} entries found matching the criteria.")

        return choice(valid_infos)

    def __str__(self) -> str:
        """E.g. ``"<OntologyLookup UNIMOD v1.0 with 1560 entries>"``."""
        return f"<OntologyLookup {self.ontology_name} v{self._version} with {len(self._raw_data)} entries>"

    def __repr__(self) -> str:
        """Same as :meth:`__str__`."""
        return self.__str__()

    def __len__(self) -> int:
        """``len(lookup)``: total number of entries."""
        return len(self._raw_data)
