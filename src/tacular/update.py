"""``tacular update`` — refresh bundled ontology data from the latest OBO releases.

Downloads the current ``.obo`` source files, regenerates the data, and writes it
to the per-user cache (see :mod:`tacular._cache`). Each ontology lookup prefers
this cached data over the copy baked into the package, so a refresh takes effect
on the next ``import tacular`` — no reinstall required.

Usage::

    tacular update                 # refresh all pullable ontologies
    tacular update unimod xlmod    # refresh a subset
    tacular update --offline DIR   # regenerate from local .obo files in DIR
    tacular status                 # show bundled vs cached versions
    tacular clear                  # remove the cache (revert to bundled data)
    tacular where                  # print the cache directory

If regenerating data hits an entry it can't parse (e.g. an ontology release
adds a formula format the parser doesn't recognize), a warning is always
printed with the offending id/name, the raw input that failed, the exception
type and message, and a full traceback — enough to diagnose the root cause
directly from the log without re-running under a debugger. ``-v``/``-vv``
raise the overall verbosity (INFO/DEBUG) for additional progress detail
beyond that.
"""

from __future__ import annotations

import argparse
import importlib
import logging
import shutil
import sys
import urllib.request
from pathlib import Path

from . import _cache

logger = logging.getLogger(__name__)

# OBO source files. Several ontologies can share one source (resid derives from PSI-MOD).
OBO_SOURCES: dict[str, tuple[str, str]] = {
    "unimod": ("https://www.unimod.org/obo/unimod.obo", "UNIMOD.obo"),
    "psimod": ("https://purl.obolibrary.org/obo/mod.obo", "PSI-MOD.obo"),
    "gno": ("https://purl.obolibrary.org/obo/gno.obo", "GNOme.obo"),
    "xlmod": ("https://purl.obolibrary.org/obo/xlmod.obo", "XLMod.obo"),
}

# Output ontology -> (builder module, OBO source key). Order = default update order.
ONTOLOGIES: dict[str, tuple[str, str]] = {
    "unimod": ("tacular._datagen.unimod", "unimod"),
    "xlmod": ("tacular._datagen.xlmod", "xlmod"),
    "psimod": ("tacular._datagen.psimod", "psimod"),
    "resid": ("tacular._datagen.resid", "psimod"),
    "gno": ("tacular._datagen.gno", "gno"),
}

# Heads-up for the heavy one.
_LARGE = {"gno"}


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "tacular-update"})
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req) as resp, open(tmp, "wb") as out:  # noqa: S310 - fixed https ontology hosts
        shutil.copyfileobj(resp, out)
    tmp.replace(dest)
    print(f"  saved {dest} ({dest.stat().st_size / 1_048_576:.1f} MB)")


def _mass_mismatches(infos: list) -> list[tuple[str, str, float]]:
    """Entries whose monoisotopic mass disagrees with the mass derived from their composition.

    Restores the "MASS MISMATCH" signal the standalone generators used to emit: it surfaces
    entries that are internally inconsistent in the source ontology (a known occurrence in
    these controlled vocabularies) so a refresh doesn't cache them silently.
    """
    from ._datagen._utils import calculate_mass

    out: list[tuple[str, str, float]] = []
    for info in infos:
        comp = info.dict_composition
        reported = info.monoisotopic_mass
        if not comp or reported is None:
            continue
        try:
            calc = calculate_mass(comp, monoisotopic=True)
        except (KeyError, TypeError):
            continue
        if abs(calc - reported) > 0.01:
            out.append((info.id, info.name, reported - calc))
    return out


def update(names: list[str] | None = None, *, offline: str | Path | None = None) -> list[str]:
    """Refresh ``names`` (default: all). With ``offline``, read OBOs from that dir instead of downloading.

    Returns the list of ontologies successfully refreshed.
    """
    names = list(ONTOLOGIES) if not names else names
    unknown = [n for n in names if n not in ONTOLOGIES]
    if unknown:
        raise ValueError(f"unknown ontologies {unknown}; choose from {list(ONTOLOGIES)}")

    obo_root = Path(offline).expanduser() if offline is not None else _cache.obo_dir()

    # Fetch each needed OBO source once.
    needed_sources = {ONTOLOGIES[n][1] for n in names}
    obo_paths: dict[str, Path] = {}
    for src in needed_sources:
        url, fname = OBO_SOURCES[src]
        path = obo_root / fname
        if offline is not None:
            if not path.is_file():
                raise FileNotFoundError(f"offline mode: {path} not found")
            print(f"  using {path}")
        elif not path.is_file():
            _download(url, path)
        else:
            print(f"  using cached {path} (delete to force re-download)")
        obo_paths[src] = path

    refreshed: list[str] = []
    for name in names:
        module_path, src = ONTOLOGIES[name]
        builder = importlib.import_module(module_path)
        print(f"regenerating {name} ...")
        version, infos = builder.build(obo_paths[src])
        mismatches = _mass_mismatches(infos)
        if mismatches:
            eid, ename, delta = mismatches[0]
            print(
                f"  note: {len(mismatches)} {name} entries are internally inconsistent in the source "
                f"(mass != composition), e.g. {eid} {ename} (Δ{delta:+.4f} Da)"
            )
        out = _cache.save(builder.JSON_NAME, builder.DATA_KEY, infos, version)
        print(f"  {name}: {len(infos)} entries (v{version}) -> {out}")
        refreshed.append(name)
    return refreshed


def _cmd_status() -> int:
    import tacular as t

    lookups = {
        "unimod": t.UNIMOD_LOOKUP,
        "xlmod": t.XLMOD_LOOKUP,
        "psimod": t.PSIMOD_LOOKUP,
        "resid": t.RESID_LOOKUP,
        "gno": t.GNO_LOOKUP,
    }
    print(f"cache dir: {_cache.cache_dir()}")
    print(f"cache {'DISABLED' if _cache.cache_disabled() else 'enabled'}\n")
    print(f"{'ontology':10} {'cached':8} {'active version':24} entries")
    for name, (module_path, _src) in ONTOLOGIES.items():
        builder = importlib.import_module(module_path)
        cached = _cache.data_file(builder.JSON_NAME).is_file()
        lk = lookups[name]
        print(f"{name:10} {'yes' if cached else 'no':8} {lk.version:24} {len(lk.values())}")
    return 0


def _cmd_clear() -> int:
    d = _cache.data_dir()
    if d.exists():
        shutil.rmtree(d)
        print(f"removed cached data: {d}")
    else:
        print("no cached data to remove")
    return 0


def _configure_logging(verbosity: int) -> None:
    """Set up root logging for CLI runs: -v -> INFO, -vv -> DEBUG (with tracebacks)."""
    level = logging.WARNING if verbosity <= 0 else logging.INFO if verbosity == 1 else logging.DEBUG
    logging.basicConfig(level=level, format="%(levelname)s [%(name)s] %(message)s", stream=sys.stderr, force=True)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``tacular`` console script and ``python -m tacular``.

    Args:
        argv: Arguments to parse (defaults to ``sys.argv[1:]`` via argparse).

    Returns:
        Process exit code: ``0`` on success, ``1`` on a handled error (unknown
        ontology, missing offline file, or a download/OS failure -- see the
        ``except`` clause below), ``2`` from argparse itself for bad CLI usage.
    """
    parser = argparse.ArgumentParser(
        prog="tacular", description="Refresh bundled ontology data from the latest OBO releases."
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="raise verbosity beyond warnings (-v: info, -vv: debug); parsing failures always warn with a traceback",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_update = sub.add_parser("update", help="download latest OBOs and regenerate cached data")
    p_update.add_argument("ontologies", nargs="*", help=f"subset to refresh (default all): {list(ONTOLOGIES)}")
    p_update.add_argument("--offline", metavar="DIR", help="regenerate from local .obo files in DIR (no download)")

    sub.add_parser("status", help="show bundled vs cached data versions")
    sub.add_parser("clear", help="remove cached data (revert to bundled)")
    sub.add_parser("where", help="print the cache directory")

    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    if args.command == "update":
        names = args.ontologies or None
        if names is None and args.offline is None and _LARGE:
            print(f"note: refreshing all ontologies including {sorted(_LARGE)} (large download)\n")
        try:
            refreshed = update(names, offline=args.offline)
        except (ValueError, FileNotFoundError, OSError) as exc:
            # Log the full traceback at DEBUG (visible with -vv) before the concise
            # one-line message every user sees, so the root cause is never lost.
            logger.debug("`tacular update` failed", exc_info=True)
            print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1
        print(f"\ndone: refreshed {refreshed}. Changes take effect on next `import tacular`.")
        return 0
    if args.command == "status":
        return _cmd_status()
    if args.command == "clear":
        return _cmd_clear()
    if args.command == "where":
        print(_cache.cache_dir())
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
