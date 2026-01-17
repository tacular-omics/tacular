from collections.abc import Iterable
from functools import cached_property
from random import choice

from .obo_entity import OboEntity, filter_infos


class OntologyLookup[T: OboEntity]:
    """Base class for ontology lookups with common functionality."""

    def __init__(
        self,
        data: dict[str, T],
        ontology_name: str,
        id_prefixes: tuple[str, ...] = (),
        name_prefixes: tuple[str, ...] = (),
        _version: str = "",
    ) -> None:
        """
        Initialize ontology lookup.

        Args:
            data: Dictionary mapping IDs to info objects
            ontology_name: Name of the ontology (e.g., "UNIMOD", "PSI-MOD")
            id_prefixes: Tuple of case-insensitive prefixes to strip from IDs (e.g., ("unimod", "u"))
            name_prefixes: Tuple of case-insensitive prefixes to strip from names (e.g., ("u",))
        """
        self.ontology_name = ontology_name
        self.id_prefixes = tuple(p.lower() for p in id_prefixes)
        self.name_prefixes = tuple(p.lower() for p in name_prefixes)

        self.id_to_info: dict[str, T] = data
        self.name_to_info: dict[str, T] = {info.name: info for info in data.values()}

        # make keys lowercase for case-insensitive lookup
        self.id_to_info = {k.lower(): v for k, v in self.id_to_info.items()}
        self.name_to_info = {k.lower(): v for k, v in self.name_to_info.items()}
        self._version = _version

    @property
    def version(self) -> str:
        """Get the version of the ontology data."""
        return self._version

    def _strip_prefix(self, value: str, prefixes: tuple[str, ...]) -> str:
        """Strip known prefixes from a value."""
        if ":" in value:
            prefix, rest = value.split(":", 1)
            if prefix.lower() in prefixes:
                return rest
        return value

    def query_id(self, mod_id: str | int) -> T | None:
        """Query by ID, stripping known prefixes."""
        if isinstance(mod_id, int):
            mod_id = str(mod_id)

        mod_id = self._strip_prefix(mod_id, self.id_prefixes)
        return self.id_to_info.get(mod_id.lower())

    def query_name(self, name: str) -> T | None:
        """Query by name, stripping known prefixes."""
        name = self._strip_prefix(name, self.name_prefixes)
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

    def __getitem__(self, key: str) -> T:
        info = self.query_name(key)
        if info is not None:
            return info

        info = self.query_id(key)
        if info is not None:
            return info

        raise KeyError(f"{self.ontology_name} modification '{key}' not found by name or ID.")

    def __contains__(self, key: str) -> bool:
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key: str) -> T | None:
        try:
            return self[key]
        except KeyError:
            return None

    def __iter__(self) -> Iterable[T]:
        """Iterator over all entries in the lookup."""
        return iter(self.name_to_info.values())

    def values(self) -> Iterable[T]:
        """Get all entries in the lookup."""
        return self.name_to_info.values()

    def keys(self) -> Iterable[str]:
        """Get all keys (names) in the lookup."""
        return self.name_to_info.keys()

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
