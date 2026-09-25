# tacular — Claude Code Guide

## Project overview

tacular is a Python library of lookups for MS-proteomics values: post-translational
modifications (UNIMOD, PSI-MOD, RESID, XLMOD, GNOme, UniProt-PTM), amino acids,
chemical elements and isotopes, fragment ion types, neutral losses, proteases,
monosaccharides, and mzPAF reference molecules. It has **no runtime dependencies**.

Place in the tacular-omics graph: tier 0 (no sibling dependencies). Direct downstream
consumers are `peptacular` (ProForma peptides) and `paftacular` (mzPAF annotations);
`spxtacular`, `peff_digest` and friends consume it through those. **tacular does not
depend on them; treat them as downstream consumers, not as an authority on tacular's
own data** (see Gotchas).

Every ontology/data type exposes a module-level `*_LOOKUP` singleton (e.g.
`t.UNIMOD_LOOKUP`, `t.ELEMENT_LOOKUP`) queryable by id, name, or (for ontologies)
approximate mass.

## Commands

```bash
just install        # uv sync
just test           # uv run pytest tests
just test-cov       # pytest with branch coverage (term + html + xml)
just lint           # ruff check src tests (same as CI)
just format         # ruff isort-fix on src/tests/data_gen, ruff format src/tests  -- WRITES FILES
just ty             # ty check src
just check          # format + lint + ty + test (so it also rewrites files)
just gen            # regenerate all data.py files from OBO/JSON sources (data_gen/justfile gen)
just gen-jsons      # regenerate jsons/*.json from the installed package (create_output_jsons.py)
just docs           # sphinx-build docs -> docs/_build/html
just docs-test      # sphinx doctest build (the real doctest runner; ~10 tests)
just pre-release    # format lint check test gen-jsons docs-test check-version
just check-version  # scripts/release_version.py check
```

`data_gen/justfile` has per-ontology recipes: `gen-uni`, `gen-psi`, `gen-resid`,
`gen-xlmod`, `gen-gno`, `gen-uniprot-ptm`, `gen-aa`, `gen-frag`, `gen-pro`, `gen-ref`,
`gen-delta`, `gen-mono` (and `download-*`). Run as `just -f data_gen/justfile gen-uni`.

`just test-docs` is an alias for `just docs-test` (the sources have no doctests).

CLI: the `tacular` console script (also `python -m tacular`) has `update`, `status`,
`clear`, `where`, plus `-v`/`-vv`. See "Refreshing ontology data" below.

CI (`.github/workflows/ci.yml`): `ruff check src tests`, `ruff format --check src tests`,
`ty check src`, `release_version.py check`, pytest on 3.12-3.14 / macOS / Windows,
lowest-direct resolution, and the built wheel.

## Architecture

```
src/tacular/
  __init__.py         # re-exports every public name; holds __version__; the 6 ontology
                      # subpackages load lazily via module __getattr__ (_LAZY_SUBMODULES)
  obo_entity.py       # OboEntity: shared base dataclass for ontology *Info classes
  obo_lookup.py       # OntologyLookup: shared base class for the 6 ontology *Lookup classes;
                      # _normalize_id is the ONE id normaliser for every ontology
  _lookup.py          # _BaseLookup: [] / get / in / len / iter / keys / values / items for ALL 15 lookups
  errors.py           # TacularError(ValueError), TacularKeyError(TacularError, KeyError)
  constants.py        # PROTON_MASS, ELECTRON_MASS, NEUTRON_MASS, HYDROGEN_MASS, C13_C12_MASS_DIFF (cited)
  tolerance.py        # ppm_error, da_to_ppm, ppm_to_da, tolerance_window, within_tolerance
                      # (units "da"/"ppm"); query_mass uses its window
  _util.py            # _round (to_dict float rounding)
  _cache.py           # per-user cache resolution: lookups prefer a refreshed
                      # cache over the bundled data.py, if one exists
  _datagen/           # OBO/formula parsing logic -- the single source of truth,
                      # used by BOTH data_gen/'s dev generators and `tacular update`
    _utils.py           # shared OBO reading + formula parsing helpers
    unimod.py, xlmod.py, psimod.py, resid.py, gno.py   # one builder per OBO ontology
    uniprot_ptm.py      # ptmlist.txt flat-file builder (not OBO, same build()/DATA_KEY/JSON_NAME contract)
  update.py           # `tacular update`/`status`/`clear`/`where` CLI (console script)
  __main__.py         # `python -m tacular` entrypoint
  labels/             # isobaric tags + SILAC labels; _data.py is hand-maintained (not generated)
  <ontology>/         # one package per ontology/data type, e.g. unimod/, elements/
    __init__.py         # re-exports the public names for this ontology
    data.py             # AUTO-GENERATED -- do not hand-edit, see "Regenerating data"
    dclass.py           # the *Info dataclass
    lookup.py           # the *Lookup class + the *_LOOKUP singleton

data_gen/             # developer-only data generation pipeline (not shipped in the wheel)
  data/                 # downloaded .obo sources (gitignored) + a few hand-maintained .json inputs
  generator/gen_*.py    # one script per ontology/data type; renders data.py from
                        # tacular._datagen.<name>.build() (OR, for non-OBO types like
                        # amino acids/neutral deltas/proteases/refmol/monosaccharides,
                        # has its own lightweight parsing -- these aren't OBO-sourced)
  generator/utils.py    # thin re-export of tacular._datagen._utils
  README.md             # data-generation details + known upstream data-quality issues

jsons/                # JSON snapshot of every lookup's data (`just gen-jsons`);
                      # not consumed by tacular itself, offered for non-Python consumers
```

Ontology packages (subclass `OboEntity` / `OntologyLookup`): `unimod`, `psimod`,
`resid`, `xlmod`, `gno`, `uniprot_ptm`. The others (`amino_acids`, `elements`,
`ion_types`, `monosaccharides`, `neutral_deltas`, `proteases`, `refmol`) have their
own standalone Info/Lookup classes with different query methods.

Data flow: `import tacular` builds each non-ontology `*_LOOKUP` from its bundled
`data.py`. The 6 ontology lookups are built on first access to one of their names
(`tacular.__getattr__`; keep `_LAZY_SUBMODULES` and the `TYPE_CHECKING` imports in sync
when adding one), and first ask `_cache` for a refreshed JSON in
`$TACULAR_DATA_DIR` / `$XDG_CACHE_HOME/tacular` / `~/.cache/tacular` (disable with
`TACULAR_DISABLE_CACHE=1`). `OntologyLookup` builds its id/name/number indexes lazily
on first query, and a mass-sorted index (bisected by `query_mass`) on first mass query.

### Regenerating data

- **Bug in the parsing logic**: fix it in `src/tacular/_datagen/<name>.py`, not in
  `data_gen/generator/gen_<name>.py` — the generator just renders whatever
  `_datagen` parses. After fixing, regenerate: `just -f data_gen/justfile gen-<name>`
  and check `git diff` on the resulting `data.py`: it should be either unchanged (no
  behavior change) or exactly your intended fix. This dual-use design (dev pipeline +
  runtime `tacular update`) means a parsing bug only needs fixing once.
- **Verifying a fix reproduces correctly**: `tacular._datagen.<name>.build(path)`
  returns `(version, list[Info])`; compare `{i.id: i.to_dict() for i in infos}`
  against the corresponding `jsons/<name>.json` for an exact-match check (see
  `test_builder_reproduces_bundled_json` in `tests/test_update.py`).
- **Refreshing to a newer ontology release**: `tacular update <name> --offline DIR`
  regenerates from local source files without touching the network; useful for
  testing against a newly-downloaded release before deciding whether to bump the
  bundled snapshot.

### Refreshing ontology data (user-facing CLI)

`tacular update [names...]` downloads the sources and writes JSON to the cache;
names are `unimod xlmod psimod resid gno uniprot_ptm`. With no names it refreshes
**all six, including GNOme** (a ~129 MB download; it only prints a note).
`tacular status` shows bundled vs cached versions, `tacular clear` deletes cached data
and downloaded sources (`obo/`), reverting to bundled data, `tacular where` prints the cache dir. Refreshes take effect on the next import.

## Public API

Everything below is importable from `tacular` (all names in `__all__` were imported
and checked). `import tacular as t` is the house style.

- **Errors and constants**: `TacularError`, `TacularKeyError`, `tacular.constants`
  (module, not in `__all__`).
- **Mass tolerances** (`tacular.tolerance`): `ppm_error`, `da_to_ppm`, `ppm_to_da`,
  `tolerance_window(mass, tol, *, tolerance_unit="da"|"ppm")`, `within_tolerance(obs, theo, tol, *, tolerance_unit=)`,
  `ToleranceUnit`.
- **Shared types** (`tacular.types`): `ToleranceUnit`, `Polarity = Literal["positive", "negative"]`,
  both also exported from `tacular`; sibling packages import these instead of their own copies.
- **Quantitative labels** (`tacular.labels`, hand-maintained `_data.py`): `ISOBARIC_TAG_LOOKUP`,
  `IsobaricTagLookup`, `IsobaricTagInfo`, `ReporterIonInfo`, `SILAC_LOOKUP`, `SilacLabelLookup`,
  `SilacLabelInfo`. Masses are computed from `dict_composition`, never typed in.
- **Every lookup** subclasses `_BaseLookup`: `lookup[key]` (raises `TacularKeyError`),
  `.get(key, default)`, `in`, `len`, iteration over entries, `.keys()`, `.values()`, `.items()`.
- **Ontology lookups** (`OntologyLookup` subclasses; `lookup[key]` tries name, then id;
  `.query_id`, `.query_name`, `.query_mass(mass, *, tolerance=0.01, tolerance_unit="da"|"ppm", monoisotopic=True)`,
  `.choice(*, ...)`, `.version`; `.keys()` are raw ids):
  - `UNIMOD_LOOKUP`, `UnimodInfo`, `UnimodLookup` — UNIMOD
  - `PSIMOD_LOOKUP`, `PsimodInfo`, `PsimodLookup` — PSI-MOD
  - `RESID_LOOKUP`, `ResidInfo`, `ResidLookup` — RESID (derived from PSI-MOD; ids `AA0002`, prefix optional)
  - `XLMOD_LOOKUP`, `XlmodInfo`, `XlmodLookup` — XLMOD cross-linkers
  - `GNO_LOOKUP`, `GnoInfo`, `GnoLookup` — GNOme glycans (ids `G00008BG`, prefix optional)
  - `UNIPROT_PTM_LOOKUP`, `UniprotPtmInfo`, `UniprotPtmLookup` — UniProt ptmlist; extra
    fields plus `.get_unimod()`, `.get_psimod()`, `.residue`, `.location`
  - `OboEntity` — base dataclass: `id, name, formula, monoisotopic_mass, average_mass,
    dict_composition`, `.composition`, `.get_mass(*, monoisotopic)`, `.to_dict(*, float_precision)`,
    `.from_dict()`, `.update()`, `.id_tag`
- **Amino acids**: `AA_LOOKUP`, `AALookup`, `AminoAcid` (enum A-Z incl. B J O U X Z),
  `AminoAcidInfo`, `AMINO_ACID_INFOS` (dict), `ORDERED_AMINO_ACIDS` (list); `AA_LOOKUP` also
  has `.query_one_letter` / `.query_three_letter` / `.query_name` (return `None`),
  `.get_mass(key, *, monoisotopic)`, `.composition(key)`, and `.ordered_amino_acids`,
  `.ambiguous_amino_acids`, `.mass_amino_acids`, ... tuples
- **Elements**: `ELEMENT_LOOKUP` (`.get_mass(key, *, monoisotopic)`), `ElementLookup`,
  `ElementKey` (type alias), `Element` (enum), `ElementInfo`,
  `parse_composition` (`{"C": 2}` -> `{ElementInfo: 2}`)
- **Fragment ions**: `FRAGMENT_ION_LOOKUP`, `FragmentIonLookup`, `FragmentIonInfo`,
  `IonType` (enum), `IonTypeLiteral`, `IonTypeProperty` (flag enum)
- **Neutral deltas**: `NEUTRAL_DELTA_LOOKUP`, `NeutralDeltaLookup`, `NeutralDelta`,
  `NeutralDeltaInfo`, `NeutralDeltaLiteral`, `NEUTRAL_DELTA_DICT`
- **Proteases**: `PROTEASE_LOOKUP`, `ProteaseLookup`, `Protease`
  (enum), `ProteaseInfo` (`.regex`, compiled `.pattern` property), `PROTEASE_DICT`, `ProteaseLiteral`
- **Monosaccharides**: `MONOSACCHARIDE_LOOKUP`, `MonosaccharideLookup`, `Monosaccharide`,
  `MonosaccharideInfo`
- **mzPAF reference molecules**: `REFMOL_LOOKUP`, `RefMolLookup`, `RefMolID`, `RefMolInfo`
  (`.formula`), `RefMolLiteral`

Removed in 2.0 (see `docs/migration.rst`): no aliases are kept for renamed names. Every
public module has an explicit `__all__`; generated `data.py` modules are internal but
also carry an `__all__`. `*Info` dataclasses are `frozen=True, slots=True`; cached derived values live in
`field(init=False, repr=False, compare=False)` fields set in `__post_init__` with
`object.__setattr__` (zero-arg `super()` breaks under `slots=True`, and `cached_property`
needs `__dict__`). Per-instance memos that must stay out of `fields`/`asdict`/pickle
(`ElementInfo`'s hash, the resolved `composition` incl. `OboEntity.composition`) live instead in a `__slots__` of a
private base class (`_CachedHash`, `elements.lookup._CompositionCache`), set lazily.

## Conventions

- **Docstrings**: Google-style (`Args:`, `Returns:`, `Raises:`), not Sphinx `:param:`.
  Check `obo_entity.py`, `obo_lookup.py`, `elements/lookup.py` before adding new ones.
  Dataclass fields document themselves via a bare string literal placed immediately
  after the field declaration (Sphinx autodoc picks this up) — see `OboEntity`.
- **Typing**: fully typed, `py.typed` shipped, Python >= 3.12 (PEP 695 generics like
  `OntologyLookup[T: OboEntity]`). Ruff line length 120; `**/data.py` is excluded from
  ruff.
- **Errors**: raise `TacularError` (from `tacular.errors`) for bad input and
  `TacularKeyError` for a lookup miss, never a bare `ValueError`/`KeyError`/`TypeError`.
  `.get()`, `in` and `.query_*()` never raise; they return `None`/`False`.
- **Options are keyword-only**: `get_mass(*, monoisotopic=True)`,
  `to_dict(*, float_precision=6)` (`None` = no rounding). New physical constants go in
  `constants.py` with a cited source; never hard-code a proton/neutron mass elsewhere
  (`data_gen/generator/constants.py` re-exports `tacular.constants.PROTON_MASS`).
- **Logging**:
  - The `_datagen/*.py` builders log a `logger.warning(..., exc_info=True)` when an
    individual entry can't be parsed (bad formula, unknown symbol, etc.) — the
    message includes the offending id/name, the raw input, the exception type and
    message, and a full traceback, then the entry falls back to `None` fields rather
    than aborting the whole regeneration. Keep this pattern for any new failure
    path: **never swallow an exception into a bare warning without the exception's
    own message/type attached**.
  - `_cache.py` deliberately uses `logging.warning`, not `warnings.warn`, for a
    corrupt/unreadable cache — `warnings.warn` would raise under `-W error`/pytest's
    `filterwarnings = error`, defeating the transparent fallback to bundled data.
    Don't reintroduce `warnings.warn` there.
  - The CLI's `-v`/`-vv` go through `update._configure_logging`, which calls
    `logging.basicConfig(force=True)` — this reconfigures the *global* root logger.
    Every test that calls `update.main(...)` must run under a fixture that
    saves/restores `logging.getLogger().handlers`/`.level` (see `restore_root_logger`
    in `tests/test_update_cli.py`), or it will silently strip pytest's caplog handler
    for the rest of the session.
- **Tests**: `tests/`, one file roughly per module/feature area (e.g.
  `test_datagen_gno.py`, `test_update_cli.py`).
  - Use `tmp_path`/`monkeypatch`, not `tempfile`. For anything touching `_cache.py`,
    always `monkeypatch.setenv("TACULAR_DATA_DIR", ...)` to a `tmp_path` so tests never
    read/write the real `~/.cache/tacular`.
  - GNOme's real `.obo` is ~129 MB — tests exercise `gno.py` against small synthetic
    OBO snippets (`tests/test_datagen_gno.py`); the real-file reproduction check in
    `tests/test_update.py` excludes GNOme, and skips any case whose source file is not in
    `data_gen/data/`.
  - Coverage: keep new code near the ~90% project average (`just test-cov`); don't
    chase branches that are genuinely unreachable given upstream validation.

## Gotchas (hard-won — read before touching mass/formula data)

- **`peptacular` is not ground truth for tacular's own data**, even though it's
  the main downstream consumer. Using it to "verify" a tacular value is circular.
  A fragment-ion fix was once validated against `peptacular`'s
  `_INTERNAL_MASS_DIFFS` table and turned out wrong on 5 of 9 values — peptacular
  had its own independent bug. Verify against the OBO source file, an external
  standard (e.g. the mzPAF spec/grammar, `github.com/HUPO-PSI/mzpaf`), or
  first-principles element-mass arithmetic.
- **mzPAF only standardizes the default internal fragment ion** (`m<start>:<end>`,
  tacular's `"by"` type, neutral mass = sum of residue masses, no offset). The other
  8 internal types (`ax, ay, az, bx, bz, cx, cy, cz`) are *not* in the mzPAF grammar —
  there is no external table. They're derived from tacular's own a/b/c/x/y/z
  terminal-ion offsets via `internal(F,B) = δF + δB - H2O`. Re-derive from that
  identity rather than copying values from another tool.
- **Composition vs. mass can silently disagree** if a parser drops isotope atoms
  (e.g. `13C`) from `composition`/`formula` while still summing them into
  `monoisotopic_mass`. This produced no test failures for months. When editing a
  parser, check that
  `sum(ELEMENT_LOOKUP.get_mass(sym) * n for sym, n in info.dict_composition.items())`
  equals `info.monoisotopic_mass` within ~0.01 Da (isotope keys like `"13C"` resolve
  directly in `ELEMENT_LOOKUP`).
- **Don't trust "this generator's output looks unchanged" from eyeballing a diff.**
  Regenerated `data.py` files are large; verify via the `build()` vs `jsons/*.json`
  id-for-id comparison, not a visual scan.
- **Id queries strip only the ontology's own accession prefixes** (`accession_prefixes=` on
  each `*Lookup`: `UNIMOD:`/`U:`, `MOD:`/`M:`, `XLMOD:`/`X:`, `RESID:`/`R:`, `GNO:`/`G:`,
  `PTM-`), then RESID `AA` / GNO `G` (`id_prefix=`), then leading zeros, all in
  `obo_lookup._normalize_id`. Names accept the same prefixes (`U:Phospho`).
  `UNIMOD_LOOKUP["MOD:00046"]` still raises `TacularKeyError`.
- **Name lookups are case-insensitive** (`"oxidation"` works) and `lookup[key]` tries the
  name before the id.
- **`NeutralDeltaInfo` masses are signed losses** (`H2O` is -18.0106); fragment-ion
  masses are offsets (`y` = +18.0106, `b` = 0).
- **`ELEMENT_LOOKUP["C"]`** is the element-level entry (`mass_number=None`, mass = the
  monoisotopic isotope's mass); isotopes are `"13C"` or `("C", 13)`, not `"C13"`.
- **`AA_LOOKUP["X"]`** has mass `0.0` and is not flagged ambiguous; `B` and `Z` have mass
  `None`.
- `just format` / `just check` rewrite files in place. Run them only on your own branch.

## Releasing

Only the tacular-omics overseer bumps versions or publishes. See `just --list`
(`set-version`, `sync-version`, `check-version`, `pre-release`).

- Version source: `__version__` in `src/tacular/__init__.py` (`[tool.hatch.version]`);
  `scripts/release_version.py` copies it to `CITATION.cff` (it is a synced copy of the
  workspace `templates/scripts/release_version.py`; do not edit it here).
- Changelog is `CHANGELOG.md` (`## [Unreleased]`, then `## [X.Y.Z] (YYYY-MM-DD)`).
- Publishing is the `publish.yml` workflow on a GitHub release (PyPI trusted publishing).
- Remote: `https://github.com/tacular-omics/tacular` (an old `pgarrett-scripps/tacular`
  remote redirects here).

## Workspace note

This repo is also developed inside the tacular-omics uv workspace
(`~/Repos/tacular-omics/packages/tacular`); there `uv run` uses the shared `.venv` and
the root `uv.lock`, not this repo's own. See the workspace CLAUDE.md.
