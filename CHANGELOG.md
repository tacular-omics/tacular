# Changelog

## [Unreleased]

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
