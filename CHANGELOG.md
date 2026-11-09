# Changelog

## [Unreleased]

### Changed

- Lookup miss messages for monosaccharides, reference molecules, isobaric tags and SILAC labels now name the kinds of key they accept and list the valid names (closed sets).

## [2.1.0] (2026-11-06)

### Changed

- `composition` is now a `collections.Counter` on every lookup's entries. The six
  ontology lookups' entries (`UnimodInfo`, `PsimodInfo`, `ResidInfo`, `XlmodInfo`,
  `GnoInfo`, `UniprotPtmInfo`) and `MonosaccharideInfo` returned a plain `dict`, while
  amino acids, elements, fragment ions, neutral deltas, reference molecules and the
  quantitative labels already returned a `Counter`, so adding a residue composition to a
  modification composition raised `TypeError`. A residue and a modification now add
  directly: `AA_LOOKUP["S"].composition + UNIMOD_LOOKUP["Phospho"].composition`.
  `Counter` is a `dict` subclass, the key order is unchanged, and `dict_composition`,
  `to_dict()` and the JSON snapshots are untouched.

### Documentation

- `UNIPROT_PTM_LOOKUP`'s docstring and docs page now state which UniProt PTM entries the
  lookup omits and why (the 159 `CROSSLNK` entries, which describe a link between two
  residues rather than a modification of one residue, and 151 entries that carry no
  formula, mass or composition upstream: 440 of the 750 entries in the bundled `2026_03`
  release are kept), and point at
  [uniprotptmpy](https://github.com/tacular-omics/uniprotptmpy) for the whole vocabulary.
- The UNIMOD/PSI-MOD data agreement tests skip silently when the dev-only siblings
  unimodpy and psimodpy are absent. Setting `TACULAR_REQUIRE_SIBLINGS=1` now makes a
  missing sibling fail the run instead, for environments that gate a release.

## [2.0.2] (2026-10-26)

### Changed

- Updated development and test dependencies. No changes to the library.

## [2.0.1] (2026-10-08)

### Fixed
