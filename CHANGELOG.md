# Changelog

## [Unreleased]

### Added

- Every lookup now has the same mapping-style surface: `get(key, default=None)`,
  `in`, `len()`, `keys()` and `values()`. New: `NEUTRAL_DELTA_LOOKUP.get`; a `default`
  argument on the monosaccharide, protease and reference-molecule `get`; `len()` on the
  amino acid, fragment ion, monosaccharide and reference-molecule lookups; `keys()` /
  `values()` on those plus the neutral delta and protease lookups.
- `ProteaseLookup`, `OntologyLookup` and `ModLocation` are exported from `tacular`.
- Docs: the quick start states the error policy (`KeyError` = not found, `ValueError`
  = bad input; `get`/`in` never raise). Every lookup class has a class docstring.

### Fixed

- `hash()` works on every info object. `@dataclass(frozen=True)` regenerated `__hash__`
  over the `dict_composition` dict, so `hash(UNIMOD_LOOKUP["Phospho"])` (and any
  ontology, amino acid, fragment ion or reference-molecule entry) raised `TypeError`.
  Ontology entries hash on `(id, name)` as `OboEntity` documents.
- `MonosaccharideInfo` is a `@dataclass(frozen=True, slots=True)` like the other
  ontology entries.
- The non-ontology lookups (amino acids, proteases, fragment ions, monosaccharides,
  neutral deltas, reference molecules) return "not found" for non-string keys
  (`get(None)` returns the default, `None in` is `False`, `[None]` raises `KeyError`)
  instead of raising `AttributeError`. `ELEMENT_LOOKUP.get` returns the default for a
  malformed key such as `"c"` or a wrong-type key such as `None` instead of raising
  `ValueError`/`TypeError`; `ELEMENT_LOOKUP[None]` raises an error that is both a
  `KeyError` and (as before) a `TypeError`.
- `composition` on amino acid, fragment ion, neutral delta and reference-molecule
  entries (and `AA_LOOKUP.composition()`) returns a fresh `Counter` each time. It was
  a cached object, so mutating the result changed the entry for every later caller.
- `REFMOL_LOOKUP.query_label_type` / `query_molecule_type` return a new list each call
  instead of the lookup's internal list.
- A bundled `data.py` that fails to load now raises `ImportError` instead of warning and
  silently shipping an empty lookup (elements, UNIMOD, PSI-MOD, RESID, XLMOD, GNOme,
  UniProt-PTM, monosaccharides). Only that block of the generated files changed.
- `ElementLookup` docs no longer promise auto-generated isotopes or the nonexistent
  `auto_generate` / `include_generated` parameters; `keys()` is annotated with
  `Element` keys.

- Isotope-labelled formulas are written in ProForma bracket syntax, so they parse back
  to their own composition: UNIMOD `Label:13C(6)` was `C-613C6` (read as `C-613`) and is
  now `C-6[13C6]`. 132 UNIMOD and 4 XLMOD `formula` strings (and `jsons/`) changed;
  compositions and masses were already correct.
- `OntologyLookup` now raises `ValueError` on duplicate ids or duplicate (case-insensitive)
  names. A chained `!=` only raised when both counts were off, so duplicates slipped through.
- Satellite ion offsets follow mzPAF 1.0.1 (neutral residue remnant, charge excluded):
  `d` is `C2H4N` (was `C2H3N`), `v` is `C2H3NO2` (was `C2H2NO`), `w` is `C3H4O2` (was
  `C3H3O`), and the residue-specific `w` ions gain an `O` (`w-valine` `C4H6O2`). `d` is
  1.0078 Da, `v`/`w` 17.0027 Da and the specific `w` ions 15.9949 Da heavier; the
  residue-specific `d` ions were already right.
- Thermolysin cleaves N-terminal to A, F, I, L, M, V (not after D or E), as in ExPASy
  PeptideCutter; it previously cleaved C-terminal to them.
- UniProt ptmlist refreshed to 2026_03: 29 glycan entries (e.g. PTM-0745) had their
  monoisotopic and average masses swapped; PTM-0775 and PTM-0776 are new.
- Ontology lookups return "not found" for keys that are not `str` or `int` (`None in
  UNIMOD_LOOKUP` is `False`, `get(None)` returns the default, `[None]` raises `KeyError`)
  instead of raising `AttributeError` or `TypeError`.

## [1.1.3] (2026-09-23)

### Fixed

- Id lookups now accept each ontology's own accession prefix, as `query_id` documented:
  `UNIMOD_LOOKUP["UNIMOD:21"]`, `PSIMOD_LOOKUP["MOD:00046"]`, `XLMOD:01000`,
  `RESID:AA0002`, `GNO:G00008BG` and UniProt's `PTM-0476` resolve (case-insensitive)
  through `[]`, `get`, `in` and `query_id`. Another ontology's prefix is still rejected.
- Trypsin's `full_name` said "no proline rule" although its regex does not cleave
  before proline; it now reads "Trypsin with proline restriction".
- README: `tacular update` with no names refreshes GNOme too (it is not opt-in).
- `just test-docs` ran a pytest doctest pass that collected nothing and exited 5; it is
  now an alias for `just docs-test`. `just lint` checks `tests` as CI does.
- `GnoInfo` docstring said PSI-MOD; package docstring named a nonexistent `OboLookup`.

## [1.1.2] (2026-09-23)

### Fixed

- Zenodo archiving: removed the grant ids and hard-coded version from `.zenodo.json`, which made Zenodo reject the previous release. Funding is now credited in the README.

## [1.1.1] (2026-09-23)

* Publish from GitHub Actions with PyPI trusted publishing (`publish.yml`),
  replacing the API-token workflow; release metadata is checked against the tag.
* Keep `__version__`, `CITATION.cff` and `.zenodo.json` in sync with
  `scripts/release_version.py` (`just set-version X.Y.Z`).
* CI tests Python 3.12-3.14 on Linux plus macOS and Windows, the lowest
  direct dependency versions, and the built wheel.
* Rename `HISTORY.md` to `CHANGELOG.md`; standardize citation, Zenodo and
  package metadata.

## [1.1.0] (2026-07-07)

* Add `tacular update` CLI to refresh ontology data from the latest OBO
  releases at runtime, cached per-user and preferred over bundled data.
* Fix isotope-labelled atoms (13C, 15N, ...) being dropped from
  composition/formula while the mass stayed correct.
* Fix repeated element symbols collapsing in neutral-loss/fragment-ion
  formula parsing (e.g. formic acid, formamide).
* Refresh bundled UNIMOD data to the latest release.
* Fix all 9 internal fragment ion offsets, which were systematically wrong
  (the table was shifted so `by` was `-CO` instead of `0`). Corrected to
  `internal(F,B) = δF + δB - H2O`, consistent with the a/b/c/x/y/z offsets.
* Single-source the OBO parsing logic (shared by the build pipeline and
  `tacular update`).
* Improve logging/error diagnosability: `_datagen` parser failures now log the
  exception type/message and a full traceback (not just "something failed"),
  and a corrupt runtime cache logs via `logging` instead of `warnings.warn` so
  it can never raise under `-W error`. Add `-v`/`-vv` verbosity flags to the
  `tacular` CLI.
* Add `CLAUDE.md`/`AGENTS.md`/`llms.txt` for AI coding agents and LLM tooling;
  fill in missing module/function docstrings across the public API; correct
  stale claims in `data_gen/README.md`.
* Add a `UNIPROT_PTM_LOOKUP` lookup for UniProt's controlled vocabulary of
  posttranslational modifications (`ptmlist.txt`), with `tacular update`/cache
  support like the OBO ontologies. Cross-references to PSI-MOD/UNIMOD are
  resolvable via `get_psimod()`/`get_unimod()`.

## [1.0.1] (2026-02-03)

* docs
* zenodo

## [1.0.0] (2026-02-02)

* First release on PyPI.
</content>
