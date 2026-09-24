# Changelog

## [Unreleased]

Breaking API cleanup for 2.0.0. The bundled data is unchanged. Every old -> new name is
in [docs/migration.rst](docs/migration.rst).

### Added

- `tacular.TacularError` (a `ValueError`) and `tacular.TacularKeyError` (a
  `TacularError` that is also a `KeyError`), in `tacular.errors`.
- `tacular.constants`: `PROTON_MASS`, `ELECTRON_MASS`, `NEUTRON_MASS` (CODATA 2018),
  `HYDROGEN_MASS` and `C13_C12_MASS_DIFF` (AME2016 via NIST, the bundled isotope table).
  The data generators use them too.
- `items()` on every lookup; `MONOSACCHARIDE_LOOKUP.query_name`;
  `AA_LOOKUP.query_one_letter` / `query_three_letter` / `query_name` are public.
- Short accession prefixes on every ontology (`U:21`, `M:00046`, `R:AA0002`,
  `X:01000`, `G:G00008BG`), also in front of names (`U:Phospho`). All six ontologies use
  one id normaliser.
- `tacular.ElementKey`, the type of every key `ELEMENT_LOOKUP` accepts.
- `ElementInfo.to_dict()` includes `is_monoisotopic`; `AminoAcidInfo.to_dict()`
  includes `is_mass_ambiguous` and `is_ambiguous`.
- Docs: `docs/migration.rst` (old -> new table); errors and constants in the API reference.

### Removed

- `OboEntity.mass()` and `MonosaccharideInfo.mass()`: use `get_mass(monoisotopic=...)`.
- `ELEMENT_LOOKUP.mass()` and `AA_LOOKUP.mass()`: use `get_mass(key, monoisotopic=...)`.
- `AA_LOOKUP.one_letter()`, `three_letter()`, `name()`: use `AA_LOOKUP[key]` or the
  `query_*` methods.
- `MONOSACCHARIDE_LOOKUP.proforma()`: use `MONOSACCHARIDE_LOOKUP[name]`.
- Public index dicts: `AA_LOOKUP.one_letter_to_info` / `three_letter_to_info` /
  `name_to_info`, `PROTEASE_LOOKUP.name_to_info` / `id_to_info`,
  `MONOSACCHARIDE_LOOKUP.proforma_to_monosaccharide`, `ELEMENT_LOOKUP.element_data`.
- `ElementLookup.NEUTRON_MASS`: use `tacular.constants.NEUTRON_MASS`.
- `OntologyLookup.strip_id()`, `convert_key()` and `__str__`; `obo_entity.filter_infos()`.
- `tacular.update.OBO_SOURCES` and `ONTOLOGIES` (now private).

### Changed

- Renamed: `Proteases` -> `Protease`, `PROTEASE_LITERALS` -> `ProteaseLiteral`,
  `PROTEASES_DICT` -> `PROTEASE_DICT`, `XlModInfo` -> `XlmodInfo`,
  `XlModLookup` -> `XlmodLookup`, `RefMolInfo.chemical_formula` -> `formula` (field and
  `to_dict` key), `NeutralDeltaInfo.to_dict()["dict_composition"]` -> `"composition"`.
- Errors: `lookup[key]` raises `TacularKeyError` for every miss, malformed key or wrong
  key type (an `ELEMENT_LOOKUP` tuple key such as `("C", "x")` raised `TypeError`).
  Missing masses/compositions, `choice()` with no match, duplicate ids/names and an
  unknown ontology in `update` raise `TacularError`. Both are `ValueError`s, so
  existing `except KeyError` / `except ValueError` handlers still catch them.
- Keyword-only options: `get_mass(*, monoisotopic)`, `to_dict(*, float_precision)`,
  `OntologyLookup.query_mass(mass, *, tolerance, monoisotopic)`,
  `OntologyLookup.choice(*, ...)` and the `OntologyLookup` constructor after
  `ontology_name`.
- Every lookup shares one base, so `get(key, default)`, `[]`, `in`, `len`, iteration,
  `keys()`, `values()` and `items()` behave the same everywhere.
- `AminoAcidInfo`, `FragmentIonInfo`, `NeutralDeltaInfo`, `ProteaseInfo` and
  `RefMolInfo` are frozen, slotted dataclasses (no instance `__dict__`).
- `NeutralDeltaInfo.to_dict()["amino_acids"]` is sorted, so
  `jsons/neutral_losses.json` is deterministic.
- `ElementLookup.get_neutron_offsets_and_abundances` / `get_masses_and_abundances`
  report `0.0` (not `None`) for isotopes with no natural abundance.
- Fixed: `FragmentIonInfo.ion_type` resolves a string id (`"y"`) to its `IonType`
  (it looked the id up as an enum member name and raised `KeyError`).
- Every public module has an explicit `__all__`.
- `tacular update` always downloads the current release (it reused a cached download
  forever); `tacular clear` also removes the downloaded sources in `obo/`.

## [1.2.0] (2026-09-23)

### Added

- Every lookup now has the same mapping-style surface: `get(key, default=None)`,
  `in`, `len()`, `keys()` and `values()`. New: `NEUTRAL_DELTA_LOOKUP.get`; a `default`
  argument on the monosaccharide, protease and reference-molecule `get`; `len()` on the
  amino acid, fragment ion, monosaccharide and reference-molecule lookups; `keys()` /
  `values()` on those plus the neutral delta and protease lookups.
- `ProteaseLookup`, `OntologyLookup` and `ModLocation` are exported from `tacular`.
- `get_mass(monoisotopic=True)` on ontology entries (`OboEntity`, so UNIMOD, PSI-MOD,
  RESID, XLMOD, GNOme, UniProt-PTM) and `MonosaccharideInfo`, the name the amino acid,
  fragment ion and reference-molecule entries already use. `mass()` still works.
- Docs: the quick start states the error policy (`KeyError` = not found, `ValueError`
  = bad input; `get`/`in` never raise). Every lookup class has a class docstring.

### Changed

- PyPI classifier is `Development Status :: 5 - Production/Stable` (was 4 - Beta).
- `scripts/release_version.py sync --set X.Y.Z` also sets `date-released` in
  `CITATION.cff` to today (adding the field if missing).
- Docs: `llms-full.txt` describes 1.2 (every lookup's `len`/`keys`/`values`/`get(default)`,
  the error policy and hashability, `ProteaseLookup`, `OntologyLookup` and `ModLocation`
  exports); the `tacular status` example shows the bundled UniProt 2026_03 (440 entries).
- PSI-MOD data refreshed from 1.032.4 to 1.039.0 (18:09:2026), the release psimodpy ships:
  PSI-MOD 1558 -> 1607 entries (50 new, e.g. `MOD:00862`; `MOD:00306` is now obsolete),
  RESID 534 (was 535; `AA0301` went with `MOD:00306`). 214 PSI-MOD monoisotopic masses
  changed: 63 charged entries now state the neutral formula mass instead of the ion mass
  (e.g. `MOD:00049` 143.11789 -> 143.118438, a shift of one electron mass per charge),
  `MOD:00623` gains H2 (+2.01565 Da) and the rest move by under 5e-5 Da of rounding.
  417 average masses changed (upstream precision). Deuterated entries' compositions use
  `H` instead of `1H` (same mass), `MOD:02105` composition is now O2 matching its mass,
  and 278 formula strings are reordered (`C34FeH32N4O4` -> `C34H32N4O4Fe`) with the same
  composition. The composition check in `tests/test_reference_data.py` no longer allows an
  electron-mass offset for PSI-MOD/RESID.

### Fixed

- `hash()` works on every info object. `@dataclass(frozen=True)` regenerated `__hash__`
  over the `dict_composition` dict, so `hash(UNIMOD_LOOKUP["Phospho"])` (and any
  ontology, amino acid, fragment ion or reference-molecule entry) raised `TypeError`.
  Ontology entries hash on `(id, name)` as `OboEntity` documents.
- `MonosaccharideInfo` is a `@dataclass(frozen=True, slots=True)` like the other
  ontology entries.
- Every lookup returns "not found" for keys of the wrong type (`get(None)` returns the
  default, `None in` is `False`, `[None]` raises `KeyError`) instead of raising
  `AttributeError` or `TypeError`: the ontology lookups for keys that are not `str` or
  `int`, the others (amino acids, proteases, fragment ions, monosaccharides, neutral
  deltas, reference molecules) for non-string keys. The public `query_id(None)`,
  `query_name(None)` of the ontology lookups return `None`, and
  `REFMOL_LOOKUP.query_label_type(None)` / `query_molecule_type(None)` return `[]`.
  `ELEMENT_LOOKUP.get` returns the default for a malformed key such as `"c"` or a
  wrong-type key such as `None` instead of raising `ValueError`/`TypeError`;
  `ELEMENT_LOOKUP[None]` raises an error that is both a `KeyError` and (as before) a
  `TypeError`.
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
- Ontology id queries accept only plain ASCII-digit numeric ids (after stripping the
  prefixes, leading zeros and surrounding whitespace). `"+21"`, `"2_1"` and non-ASCII
  digits such as `"٢١"` resolved to UNIMOD 21 because they went through `int()`; they
  are now not found. A `bool` is no longer an id (`UNIMOD_LOOKUP[True]` was entry 1).
- `to_dict()["composition"]` is a copy on every entry type (ontology entries, amino
  acids, fragment ions, reference molecules). It returned the entry's own
  `dict_composition`, so editing the dict changed the entry in the global lookup.

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
