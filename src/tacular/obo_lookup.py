from collections.abc import Iterator
from functools import cached_property
from random import choice

from .obo_entity import OboEntity, filter_infos


def strip_id(key: str, prefix: str | None = None) -> str:
    """Strip known prefix from ID"""
    key = key.lower()
    if prefix is not None and key.startswith(prefix):
        key = key[len(prefix) :]
    key = key.lstrip("0")
    return key


def convert_key(key: str, prefix: str | None = None) -> int | None:
    # remove non digit characters for integer keys
    try:
        key = strip_id(key, prefix)
        return int(key)
    except ValueError:
        return None


class OntologyLookup[T: OboEntity]:
    def __init__(
        self,
        data: dict[str, T],
        ontology_name: str,
        _version: str = "",
        _id_prefix: str | None = None,
    ) -> None:
        self.ontology_name = ontology_name
        self._version = _version

        # Store raw data, defer processing
        self._raw_data = data
        self._num_to_info: dict[int, T] | None = None
        self._id_to_info: dict[str, T] | None = None
        self._name_to_info: dict[str, T] | None = None
        self._id_prefix = _id_prefix.lower() if _id_prefix is not None else None

    def _ensure_initialized(self) -> None:
        """Lazy initialization of lookup dictionaries."""
        if self._num_to_info is not None:
            return

        # Build lowercase lookup dicts
        self._num_to_info = {
            ki: v for k, v in self._raw_data.items() if (ki := convert_key(k, self._id_prefix)) is not None
        }
        self._id_to_info = {strip_id(k, self._id_prefix): v for k, v in self._raw_data.items()}
        self._name_to_info = {info.name.lower(): info for info in self._raw_data.values()}

        if len(self._id_to_info) != len(self._raw_data) != len(self._name_to_info):
            raise ValueError(
                f"Duplicate or missing IDs found in {self.ontology_name} data. Number of entries: \
             {len(self._raw_data)}, IDs: {len(self._id_to_info)}, names: {len(self._name_to_info)}"
            )

    @property
    def num_to_info(self) -> dict[int, T]:
        """Get the numeric ID to info mapping."""
        self._ensure_initialized()
        if self._num_to_info is None:
            raise RuntimeError("OntologyLookup not properly initialized.")
        return self._num_to_info

    @property
    def id_to_info(self) -> dict[str, T]:
        """Get the ID to info mapping."""
        self._ensure_initialized()
        if self._id_to_info is None:
            raise RuntimeError("OntologyLookup not properly initialized.")
        return self._id_to_info

    @property
    def name_to_info(self) -> dict[str, T]:
        """Get the name to info mapping."""
        self._ensure_initialized()
        if self._name_to_info is None:
            raise RuntimeError("OntologyLookup not properly initialized.")
        return self._name_to_info

    @property
    def version(self) -> str:
        """Get the version of the ontology data."""
        return self._version

    def query_id(self, mod_id: str | int) -> T | None:
        """Query by ID, stripping known prefixes."""
        if isinstance(mod_id, int):
            return self.num_to_info.get(mod_id)

        mod_id = strip_id(mod_id, self._id_prefix)
        info = self.id_to_info.get(mod_id)
        if info is not None:
            return info

        # try to convert to int
        try:
            ki = int(mod_id)
        except ValueError:
            ki = None

        if ki is not None:
            return self.num_to_info.get(ki)

        return None

    def query_name(self, name: str) -> T | None:
        """Query by name, stripping known prefixes."""
        return self.name_to_info.get(name.lower())

    def query_mass(self, mass: float, tolerance: float = 0.01, monoisotopic: bool = True) -> T | None:
        """Query by mass within a given tolerance."""
        matches: list[T] = []
        for info in self.id_to_info.values():
            mod_mass = info.monoisotopic_mass if monoisotopic else info.average_mass
            if mod_mass is not None and abs(mod_mass - mass) <= tolerance:
                matches.append(info)

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # if all have the same composition, return the first one
            compositions = {
                tuple(sorted(m.dict_composition.items() if m.dict_composition is not None else [])) for m in matches
            }
            if len(compositions) == 1:
                return matches[0]
            raise ValueError(
                f"Multiple {self.ontology_name} modifications found for mass {mass} within tolerance {tolerance}: "
                f"{[(m.id, m.monoisotopic_mass, m.formula) for m in matches]}"
            )
        return None

    def __getitem__(self, key: str | int) -> T:
        if isinstance(key, str):
            info = self.query_name(key)
            if info is not None:
                return info

        info = self.query_id(key)
        if info is not None:
            return info

        raise KeyError(f"{self.ontology_name} modification '{key}' not found by name or ID.")

    def __contains__(self, key: str | int) -> bool:
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key: str | int) -> T | None:
        try:
            return self[key]
        except KeyError:
            return None

    def __iter__(self) -> Iterator[T]:
        """Iterator over all entries in the lookup."""
        return iter(self.name_to_info.values())

    def values(self) -> list[T]:
        """Get all entries in the lookup."""
        return list(self.name_to_info.values())

    def keys(self) -> list[str]:
        """Get all keys (names) in the lookup."""
        return list(self.name_to_info.keys())

    @cached_property
    def _all_infos_tuple(self) -> tuple[T, ...]:
        """Cached tuple of all entries."""
        return tuple(self.name_to_info.values())

    @cached_property
    def _infos_with_mass_tuple(self) -> tuple[T, ...]:
        """Cached tuple of entries with monoisotopic mass."""
        return tuple(filter_infos(list(self.name_to_info.values()), has_monoisotopic_mass=True))

    @cached_property
    def _infos_with_composition_tuple(self) -> tuple[T, ...]:
        """Cached tuple of entries with composition."""
        return tuple(filter_infos(list(self.name_to_info.values()), has_composition=True))

    @cached_property
    def _infos_with_mass_and_composition_tuple(self) -> tuple[T, ...]:
        """Cached tuple of entries with both mass and composition."""
        return tuple(
            filter_infos(
                list(self.name_to_info.values()),
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
        return f"<OntologyLookup {self.ontology_name} v{self._version} with {len(self._raw_data)} entries>"

    def __repr__(self) -> str:
        return self.__str__()
