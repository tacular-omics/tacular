# History

## 1.0.0 (2026-02-02)

* First release on PyPI.

## 1.0.1 (2026-02-03)

* docs
* zenodo

## 1.1.0 (2026-07-07)

* Add `tacular update` CLI to refresh ontology data from the latest OBO
  releases at runtime, cached per-user and preferred over bundled data.
* Fix isotope-labelled atoms (13C, 15N, ...) being dropped from
  composition/formula while the mass stayed correct.
* Fix repeated element symbols collapsing in neutral-loss/fragment-ion
  formula parsing (e.g. formic acid, formamide).
* Refresh bundled UNIMOD data to the latest release.
* Single-source the OBO parsing logic (shared by the build pipeline and
  `tacular update`).