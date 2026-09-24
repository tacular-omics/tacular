"""Shared lookup base class (:class:`OntologyLookup`) used by every per-ontology
``*_LOOKUP`` singleton in this package (``UNIMOD_LOOKUP``, ``PSIMOD_LOOKUP``, ...).

Handles id/name normalization, query-by-id/name/mass and random sampling; each
ontology's ``*Lookup`` subclass just supplies its data, name, and accession/id
prefixes (see e.g. ``unimod/lookup.py``). Every id query, in every ontology, goes
through one normalization function, :func:`_normalize_id`.
"""

from bisect import bisect_left, bisect_right
from collections.abc import Mapping
from dataclasses import dataclass
from functools import cached_property
from random import choice

from ._lookup import _BaseLookup
from .errors import TacularError
from .obo_entity import OboEntity

__all__ = ["OntologyLookup"]


def _strip_accession(key: str, accession_prefixes: tuple[str, ...]) -> str | None:
    """``key`` without the first matching accession prefix (case-insensitive), or
    ``None`` if it carries none. ``accession_prefixes`` must be lowercase, longest first."""
    lowered = key.lower()
    for prefix in accession_prefixes:
        if lowered.startswith(prefix):
            return key[len(prefix) :]
    return None


def _normalize_id(key: str, accession_prefixes: tuple[str, ...] = (), id_prefix: str | None = None) -> str:
    """The one id normalization every ontology lookup uses.

    Strips surrounding whitespace, lowercases, removes one accession prefix (e.g.
    ``"unimod:"`` or ``"u:"``; lowercase, longest first), then the ontology's id
    prefix (e.g. RESID's ``"aa"``, GNOme's ``"g"``), then leading zeros.

    >>> _normalize_id(" UNIMOD:00021", ("unimod:", "u:"))
    '21'
    >>> _normalize_id("R:AA0002", ("resid:", "r:"), "aa")
    '2'
    >>> _normalize_id("GNO:G00008BG", ("gno:", "g:"), "g")
    '8bg'
    """
    key = key.strip().lower()
    stripped = _strip_accession(key, accession_prefixes)
    if stripped is not None:
        key = stripped
    if id_prefix is not None and key.startswith(id_prefix):
        key = key[len(id_prefix) :]
    return key.lstrip("0")


# Relative slack on the bisect window of ``query_mass``; the exact
# ``abs(m - mass) <= tolerance`` test is then applied to every candidate, so the window
# only has to exceed float rounding (a few ulps of the largest operand).
_MASS_WINDOW_SLACK = 1e-9


@dataclass(frozen=True, slots=True)
class _MassIndex[T]:
    """Entries with a mass, sorted by mass; ``positions`` is each entry's data order."""

    masses: tuple[float, ...]
    positions: tuple[int, ...]
    infos: tuple[T, ...]


@dataclass(frozen=True, slots=True)
class _Index[T]:
    by_id: dict[str, T]
    by_exact_id: dict[str, T]
    by_num: dict[int, T]
    by_name: dict[str, T]
    with_mass: tuple[T, ...]
    with_composition: tuple[T, ...]
    with_both: tuple[T, ...]


class OntologyLookup[T: OboEntity](_BaseLookup[str | int, str, T]):
    """Id/name/mass lookup over one ontology's :class:`~tacular.OboEntity` entries.

    ``lookup[key]`` tries ``key`` as a name (case-insensitive), then as an id; both
    accept the ontology's accession prefixes (``"UNIMOD:21"``, ``"U:21"``,
    ``"U:Phospho"``). :meth:`keys` are the entries' ids as stored (e.g. UNIMOD
    ``"21"``, PSI-MOD ``"00046"``). Indexes are built on first query, not at import.
    """

    def __init__(
        self,
        data: Mapping[str, T],
        ontology_name: str,
        *,
        version: str = "",
        accession_prefixes: tuple[str, ...] = (),
        id_prefix: str | None = None,
    ) -> None:
        """
        Args:
            data: Entries keyed by their raw id (e.g. UNIMOD's ``"1"``, ``"536"``, ...).
            ontology_name: Display name used in error messages (e.g. ``"UNIMOD"``).
            version: Data version string, exposed via :attr:`version`.
            accession_prefixes: Namespaces stripped from queries (case-insensitive),
                e.g. ``("UNIMOD:", "U:")``.
            id_prefix: Prefix of the ids themselves, stripped from ids and queries so
                that e.g. RESID's ``"AA0002"`` and ``"2"`` match the same entry.
        """
        self.ontology_name = ontology_name
        self._kind = f"{ontology_name} entry"
        self._version = version
        self._data: dict[str, T] = dict(data)
        self._accession_prefixes = tuple(sorted((p.lower() for p in accession_prefixes), key=len, reverse=True))
        self._id_prefix = id_prefix.lower() if id_prefix is not None else None
        self._mass_indexes: dict[bool, _MassIndex[T]] = {}

    @cached_property
    def _index(self) -> _Index[T]:
        by_id: dict[str, T] = {}
        by_num: dict[int, T] = {}
        by_name: dict[str, T] = {}
        by_exact_id: dict[str, T] = {}
        acc, idp = self._accession_prefixes, self._id_prefix
        for raw_id, info in self._data.items():
            norm = _normalize_id(raw_id, (), idp)
            if norm in by_id:
                raise TacularError(f"Duplicate id {raw_id!r} in {self.ontology_name} data.")
            by_id[norm] = info
            # Keys query_id may use as-is: they normalize to ``norm`` anyway. The raw id
            # does unless it starts with an accession prefix (normalization would strip
            # it); ``norm`` does unless it starts with one or with the id prefix.
            if _strip_accession(raw_id.strip(), acc) is None:
                by_exact_id[raw_id] = info
            if _strip_accession(norm, acc) is None and not (idp is not None and norm.startswith(idp)):
                by_exact_id[norm] = info
            if norm.isascii() and norm.isdigit():
                by_num[int(norm)] = info
            lname = info.name.lower()
            if lname in by_name:
                raise TacularError(f"Duplicate name {info.name!r} in {self.ontology_name} data.")
            by_name[lname] = info
        infos = tuple(self._data.values())
        return _Index(
            by_id=by_id,
            by_exact_id=by_exact_id,
            by_num=by_num,
            by_name=by_name,
            with_mass=tuple(i for i in infos if i.monoisotopic_mass is not None),
            with_composition=tuple(i for i in infos if i.dict_composition is not None),
            with_both=tuple(i for i in infos if i.monoisotopic_mass is not None and i.dict_composition is not None),
        )

    def _mass_index(self, monoisotopic: bool) -> _MassIndex[T]:
        cached = self._mass_indexes.get(monoisotopic)
        if cached is not None:
            return cached
        rows: list[tuple[float, int, T]] = []
        for position, info in enumerate(self._data.values()):
            mass = info.monoisotopic_mass if monoisotopic else info.average_mass
            # NaN never passes query_mass's test and would break the sort order.
            if mass is not None and mass == mass:
                rows.append((mass, position, info))
        rows.sort(key=lambda row: (row[0], row[1]))
        index = _MassIndex(
            masses=tuple(row[0] for row in rows),
            positions=tuple(row[1] for row in rows),
            infos=tuple(row[2] for row in rows),
        )
        self._mass_indexes[monoisotopic] = index
        return index

    def _entries(self) -> Mapping[str, T]:
        return self._data

    def _miss_message(self, key: object) -> str:
        return f"{self.ontology_name} entry {key!r} not found by name or id."

    def _resolve(self, key: object) -> T | None:
        if isinstance(key, str):
            info = self.query_name(key)
            if info is not None:
                return info
        if isinstance(key, str | int):
            return self.query_id(key)
        return None

    @property
    def version(self) -> str:
        """Version of the ontology data (bundled, or from the ``tacular update`` cache)."""
        return self._version

    def query_id(self, mod_id: str | int) -> T | None:
        """Query by id. Returns ``None`` if nothing matches.

        Accepts the id with or without this ontology's accession prefix, id prefix and
        leading zeros, e.g. ``UNIMOD_LOOKUP.query_id`` resolves ``"UNIMOD:21"``,
        ``"U:21"``, ``"21"``, ``"0021"`` and ``21`` to the same entry. A numeric id must
        be plain ASCII digits (``"+21"`` and ``"2_1"`` do not match). A ``bool`` or a key
        that is not a ``str`` or ``int`` returns ``None``.
        """
        if isinstance(mod_id, bool):
            return None
        if isinstance(mod_id, int):
            return self._index.by_num.get(mod_id)
        if not isinstance(mod_id, str):
            return None
        index = self._index
        info = index.by_exact_id.get(mod_id)
        if info is not None:
            return info
        return index.by_id.get(_normalize_id(mod_id, self._accession_prefixes, self._id_prefix))

    def query_name(self, name: str) -> T | None:
        """Query by name (case-insensitive), with or without an accession prefix
        (``"Phospho"`` or ``"U:Phospho"``). Returns ``None`` if nothing matches,
        including for a key that is not a ``str``."""
        if not isinstance(name, str):
            return None
        by_name = self._index.by_name
        info = by_name.get(name.lower())
        if info is not None:
            return info
        stripped = _strip_accession(name, self._accession_prefixes)
        if stripped is not None:
            return by_name.get(stripped.lower())
        return None

    def query_mass(self, mass: float, *, tolerance: float = 0.01, monoisotopic: bool = True) -> list[T]:
        """Entries whose mass is within ``tolerance`` Da of ``mass`` (monoisotopic by
        default, else average), in data order.

        Bisects a mass-sorted index (built on the first call), then applies the exact
        ``abs(entry_mass - mass) <= tolerance`` test to each candidate.
        """
        index = self._mass_index(monoisotopic)
        masses = index.masses
        slack = _MASS_WINDOW_SLACK * (1.0 + abs(mass) + abs(tolerance))
        lo = bisect_left(masses, mass - tolerance - slack)
        hi = bisect_right(masses, mass + tolerance + slack)
        if lo >= hi:
            return []
        infos = index.infos
        hits = [(index.positions[i], infos[i]) for i in range(lo, hi) if abs(masses[i] - mass) <= tolerance]
        hits.sort(key=lambda hit: hit[0])
        return [info for _, info in hits]

    def choice(self, *, require_monoisotopic_mass: bool = True, require_composition: bool = True) -> T:
        """A random entry, by default one with both a monoisotopic mass and a composition.

        Raises:
            TacularError: if no entry meets the requirements.
        """
        index = self._index
        if require_monoisotopic_mass and require_composition:
            valid = index.with_both
        elif require_monoisotopic_mass:
            valid = index.with_mass
        elif require_composition:
            valid = index.with_composition
        else:
            valid = tuple(self._data.values())
        if not valid:
            raise TacularError(f"No {self.ontology_name} entries match the criteria.")
        return choice(valid)

    def __repr__(self) -> str:
        """E.g. ``"<UnimodLookup UNIMOD v17:02:2026 11:36: 1560 entries>"``."""
        return f"<{type(self).__name__} {self.ontology_name} v{self._version}: {len(self._data)} entries>"
