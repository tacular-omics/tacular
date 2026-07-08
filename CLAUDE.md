# tacular — Claude Code Guide

## Project Overview

tacular is a Python library of lookups for MS-proteomics values: post-translational
modifications (UNIMOD, PSI-MOD, RESID, XLMOD, GNOme, UniProt-PTM), amino acids,
chemical elements and isotopes, fragment ion types, neutral losses, proteases, and
mzPAF reference molecules. It has no runtime dependencies. It is mainly a helper/data package for
`peptacular` and `paftacular` (sibling repos, same author) — those packages import
`tacular` and build peptide-level logic (fragmentation, ProForma parsing, etc.) on
top of its lookups. **tacular does not depend on them; treat them as downstream
consumers, not as an authority on tacular's own data** (see Gotchas below).

Every ontology/data type exposes a module-level `*_LOOKUP` singleton (e.g.
`t.UNIMOD_LOOKUP`, `t.ELEMENT_LOOKUP`) queryable by id, name, or (for ontologies)
approximate mass.

## Commands

```bash
just install        # uv sync
just test            # pytest tests/
just test-cov        # pytest with branch coverage (term + html + xml)
just lint             # ruff check src (excludes **/data.py)
just format           # ruff isort + format (src, tests, data_gen; excludes **/data.py)
just ty               # ty type check src (excludes **/data.py)
just check            # format + lint + ty + test
just gen              # regenerate all data.py files from OBO/JSON sources (data_gen/justfile gen)
just gen-jsons        # regenerate jsons/*.json from the installed package's data
just docs             # sphinx-build docs -> docs/_build/html
just docs-test        # sphinx doctest build
just pre-release      # format + lint + check + test + gen-jsons + docs-test
```

Also: `python -m tacular <cmd>` / the `tacular` console script (`update`, `status`,
`clear`, `where` — see "Refreshing ontology data" below).

## Architecture

```
src/tacular/
  obo_entity.py       # OboEntity: shared base dataclass every *Info subclasses
  obo_lookup.py        # OntologyLookup: shared base class every *Lookup subclasses
  _cache.py             # per-user cache resolution: lookups prefer a refreshed
                        # cache over the bundled data.py, if one exists
  _datagen/             # OBO/formula parsing logic -- the single source of truth,
                        # used by BOTH data_gen/'s dev generators and `tacular update`
    _utils.py            # shared OBO reading + formula parsing helpers
    unimod.py, xlmod.py, psimod.py, resid.py, gno.py   # one builder per OBO ontology
    uniprot_ptm.py         # ptmlist.txt flat-file builder (not OBO, same build()/DATA_KEY/JSON_NAME contract)
  update.py             # `tacular update`/`status`/`clear`/`where` CLI (console script)
  __main__.py           # `python -m tacular` entrypoint
  <ontology>/            # one package per ontology/data type, e.g. unimod/, elements/
    __init__.py           # re-exports the public names for this ontology
    data.py                # AUTO-GENERATED -- do not hand-edit, see "Regenerating data" below
    dclass.py               # the *Info dataclass (subclasses OboEntity)
    lookup.py                # the *Lookup class (subclasses OntologyLookup) + the *_LOOKUP singleton

data_gen/               # developer-only data generation pipeline (not shipped in the wheel)
  data/                  # downloaded .obo sources (gitignored) + a few hand-maintained .json inputs
  generator/gen_*.py      # one script per ontology/data type; renders data.py from
                          # tacular._datagen.<name>.build() (OR, for non-OBO types like
                          # amino acids/neutral deltas/proteases/refmol/monosaccharides,
                          # has its own lightweight parsing -- these aren't OBO-sourced)
  generator/utils.py      # thin re-export of tacular._datagen._utils (kept so gen_*.py
                          # scripts can still `from utils import ...`)
  README.md               # data-generation details + known upstream data-quality issues

jsons/                  # JSON snapshot of every lookup's data, generated via `just gen-jsons`;
                        # not consumed by tacular itself, offered for non-Python consumers
```

### Regenerating data

- **Bug in the parsing logic**: fix it in `src/tacular/_datagen/<name>.py`, not in
  `data_gen/generator/gen_<name>.py` — the generator just renders whatever
  `_datagen` parses. After fixing, regenerate: `just -f data_gen/justfile gen-<name>`
  (see `data_gen/justfile` for exact recipe names) and check `git diff` on the
  resulting `data.py`: it should be either unchanged (no behavior change) or
  exactly your intended fix. This dual-use design (dev pipeline + runtime
  `tacular update`) means a parsing bug only needs fixing once.
- **Verifying a fix reproduces correctly**: `tacular._datagen.<name>.build(obo_path)`
  returns `(version, list[Info])`; compare `{i.id: i.to_dict() for i in infos}`
  against the corresponding `jsons/<name>.json` for an exact-match check (see
  `tests/test_update.py` for the pattern used across all 5 ontologies).
- **Refreshing to a newer ontology release**: `tacular update <name> --offline DIR`
  regenerates from local `.obo` files without touching the network; useful for
  testing against a newly-downloaded release before deciding whether to bump the
  bundled snapshot.

## Docstring style

Google-style (`Args:`, `Returns:`, `Raises:`), not Sphinx `:param:` style — check
existing docstrings in `obo_entity.py`, `obo_lookup.py`, `elements/lookup.py` before
adding new ones. Dataclass fields document themselves via a bare string literal
placed immediately after the field declaration (Sphinx autodoc picks this up as an
attribute docstring) — see `obo_entity.py`'s `OboEntity` fields for the pattern.

## Logging and exception handling

- The `_datagen/*.py` builders log a `logger.warning(..., exc_info=True)` when an
  individual entry can't be parsed (bad formula, unknown symbol, etc.) — the
  message includes the offending id/name, the raw input, the exception type and
  message, and a full traceback, then the entry falls back to `None` fields rather
  than aborting the whole regeneration. Keep this pattern for any new failure
  path: **never swallow an exception into a bare warning without the exception's
  own message/type attached** — that's the difference between a log that's
  diagnosable from itself and one that isn't.
- `_cache.py` deliberately uses `logging.warning`, not `warnings.warn`, for a
  corrupt/unreadable cache — `warnings.warn` would raise under `-W error`/pytest's
  `filterwarnings = error`, defeating the whole point of a transparent fallback to
  bundled data. Don't reintroduce `warnings.warn` there.
- The `tacular` CLI supports `-v`/`-vv` (info/debug) via `update._configure_logging`,
  which calls `logging.basicConfig(force=True)` — this reconfigures the *global*
  root logger. Every test that calls `update.main(...)` must therefore run under a
  fixture that saves/restores `logging.getLogger().handlers`/`.level` afterward
  (see `restore_root_logger` in `tests/test_update_cli.py`), or it will silently
  strip pytest's own caplog handler for the rest of the test session.

## Gotchas (hard-won this session — read before touching mass/formula data)

- **`peptacular` is not ground truth for tacular's own data**, even though it's
  the main downstream consumer. It's a dependent package maintained by the same
  author; using it to "verify" a tacular data value is circular. A fragment-ion
  fix in this history was initially validated against `peptacular`'s
  `_INTERNAL_MASS_DIFFS` table and turned out wrong on 5 of 9 values — peptacular
  had its own independent bug in that table. Verify against the actual OBO source
  file, an external standard (e.g. the real mzPAF spec/grammar,
  `github.com/HUPO-PSI/mzpaf`), or first-principles element-mass arithmetic
  instead.
- **mzPAF only standardizes the default internal fragment ion** (`m<start>:<end>`,
  i.e. tacular's `"by"` type, neutral mass = sum of residue masses, no offset).
  The other 8 internal types tacular tracks (`ax, ay, az, bx, bz, cx, cy, cz`) are
  *not* part of the mzPAF grammar at all — there is no external table to check
  them against. They're derived self-consistently from tacular's own validated
  a/b/c/x/y/z terminal-ion offsets via `internal(F,B) = δF + δB - H2O`. If you
  touch these, re-derive from that identity rather than copying values from
  another tool.
- **Composition vs. mass can silently disagree** if a parser drops isotope atoms
  (e.g. `13C`) from `composition`/`formula` while still summing them correctly
  into `monoisotopic_mass`. This class of bug produced no test failures and no
  generator warnings for months because nothing cross-checked the two fields
  against each other. When adding/editing a parser, sanity-check with:
  `sum(ELEMENT_LOOKUP.mass(sym, monoisotopic=True) * n for sym, n in info.dict_composition.items())`
  should equal `info.monoisotopic_mass` within ~0.01 Da (isotope keys like `"13C"`
  resolve directly in `ELEMENT_LOOKUP`).
- **Don't trust "this generator's output looks unchanged" from eyeballing a diff.**
  Regenerated `data.py` files are large (thousands of entries); verify via the
  `build()` vs `jsons/*.json` id-for-id comparison described above, not a visual
  scan.

## Testing

- Tests live in `tests/`, one file roughly per module/feature area (e.g.
  `test_datagen_gno.py`, `test_update_cli.py`).
- Use `tmp_path`/`monkeypatch` fixtures, not `tempfile`, for file-based tests —
  and for anything touching `_cache.py`, always set `TACULAR_DATA_DIR` to a
  `tmp_path` via `monkeypatch.setenv` so tests never read/write the real
  `~/.cache/tacular`.
- GNOme's real `.obo` source is ~129 MB — tests exercise its parser (`gno.py`)
  against small synthetic OBO snippets (`tests/test_datagen_gno.py`), not the real
  file; the real-file reproduction check in `tests/test_update.py` intentionally
  excludes GNOme from the default run for this reason.
- Coverage floor: aim to keep new code close to the ~90% project average
  (`just test-cov`); don't chase branches that are genuinely unreachable given
  the code's own upstream validation (e.g. an `except` guarding against an
  element symbol that a prior check already ruled out) — that's test theater, not
  coverage.

## Release process

- Version lives in `src/tacular/__init__.py` (`__version__`), sourced by
  `[tool.hatch.version]` in `pyproject.toml`.
- Changelog is `HISTORY.md` (`## X.Y.Z (YYYY-MM-DD)` sections, terse bullet points).
- This repo's remote is `https://github.com/tacular-omics/tacular` (a prior
  `pgarrett-scripps/tacular` remote redirects here — update `origin` if you see
  the redirect warning on push).
