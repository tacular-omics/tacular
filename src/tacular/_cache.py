"""Runtime data cache for tacular.

``tacular update`` downloads the latest ontology ``.obo`` releases and regenerates
the data as JSON under a per-user cache directory. At import time each ontology
lookup prefers this cached data over the copy baked into the installed package
(see :func:`resolve`), so users can refresh to the newest ontology releases
without reinstalling tacular.

The cache is entirely optional: if it is absent, disabled, or corrupt, tacular
transparently falls back to the bundled data.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

from .obo_entity import OboEntity

logger = logging.getLogger(__name__)

ENV_DATA_DIR = "TACULAR_DATA_DIR"
ENV_DISABLE = "TACULAR_DISABLE_CACHE"


def cache_dir() -> Path:
    """Return the tacular cache directory (not necessarily existing yet).

    Resolution order: ``$TACULAR_DATA_DIR`` → ``$XDG_CACHE_HOME/tacular`` →
    ``~/.cache/tacular``.
    """
    override = os.environ.get(ENV_DATA_DIR)
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "tacular"


def obo_dir() -> Path:
    """Directory where downloaded ``.obo`` source files are stored."""
    return cache_dir() / "obo"


def data_dir() -> Path:
    """Directory where regenerated ontology JSON files are stored."""
    return cache_dir() / "data"


def cache_disabled() -> bool:
    """True if the runtime cache is disabled via ``$TACULAR_DISABLE_CACHE``."""
    return os.environ.get(ENV_DISABLE, "").strip().lower() in {"1", "true", "yes", "on"}


def data_file(name: str) -> Path:
    """Path to a cached ontology JSON file, e.g. ``unimodifications.json``."""
    return data_dir() / name


def save[T: OboEntity](name: str, data_key: str, infos: list[T], version: str | None) -> Path:
    """Serialise ``infos`` to a cached JSON file in the tacular data format.

    Mirrors the bundled ``jsons/*.json`` layout: ``{"metadata": {...},
    "<data_key>": [info.to_dict(), ...]}``.
    """
    data_dir().mkdir(parents=True, exist_ok=True)
    # float_precision=None keeps full precision so an updated install matches the bundled data.py.
    payload = {
        "metadata": {"data_version": version, "generator": "tacular update"},
        data_key: [info.to_dict(float_precision=None) for info in infos],
    }
    path = data_file(name)
    # Write atomically so an interrupted update can't leave a truncated cache behind.
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(path)
    return path


def load_cached[T: OboEntity](name: str, cls: type[T]) -> tuple[dict[str, T], str] | None:
    """Load cached ontology data for ``name`` if a valid cache exists.

    Returns ``(data_by_id, version)`` or ``None`` when the cache is disabled,
    missing, or unreadable (a corrupt cache warns and returns ``None`` so the
    caller falls back to bundled data).
    """
    if cache_disabled():
        return None
    path = data_file(name)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text())
        meta = raw.get("metadata", {})
        data_keys = [k for k in raw if k != "metadata"]
        if not data_keys:
            raise ValueError("no data key in cached file")
        items = raw[data_keys[0]]
        data: dict[str, T] = {}
        seen_names: set[str] = set()
        for item in items:
            info = cls.from_dict(item)
            # Reject the collisions OntologyLookup forbids, so a bad cache falls back to
            # bundled data here instead of raising later at first query (duplicate id) or
            # silently dropping an entry (duplicate case-insensitive name).
            if info.id in data:
                raise ValueError(f"duplicate id {info.id!r}")
            lname = info.name.lower()
            if lname in seen_names:
                raise ValueError(f"duplicate name {info.name!r}")
            seen_names.add(lname)
            data[info.id] = info
        if not data:
            raise ValueError("cached file contained no entries")
        version = meta.get("data_version") or meta.get("generated_date") or "cached"
        return data, version
    except Exception as exc:  # noqa: BLE001 - any corruption falls back to bundled data
        # Use logging (not warnings.warn) so a corrupt cache never raises under
        # warnings-as-errors; the whole point is to transparently fall back.
        logger.warning(
            "tacular: ignoring unreadable cached data at %s (%s); using bundled data. "
            "Run `tacular update` to refresh it or `tacular clear` to remove it.",
            path,
            exc,
        )
        return None


def resolve[T: OboEntity](
    name: str,
    cls: type[T],
    baked_data: dict[str, T],
    baked_version: str,
) -> tuple[dict[str, T], str]:
    """Return cached ``(data, version)`` when available, else the bundled values."""
    cached = load_cached(name, cls)
    if cached is not None:
        return cached
    return baked_data, baked_version
