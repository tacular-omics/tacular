# tacular

<div align="center">
  <img src="https://raw.githubusercontent.com/tacular-omics/tacular/main/tacular_logo.png" alt="tacular Logo" width="400" style="margin: 50px;"/>

[![Python package](https://github.com/tacular-omics/tacular/actions/workflows/ci.yml/badge.svg)](https://github.com/tacular-omics/tacular/actions/workflows/ci.yml)
[![codecov](https://codecov.io/github/tacular-omics/tacular/graph/badge.svg?token=1CTVZVFXF7)](https://codecov.io/github/tacular-omics/tacular)
[![Documentation Status](https://readthedocs.org/projects/tacular/badge/?version=latest)](https://tacular.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/tacular.svg)](https://badge.fury.io/py/tacular)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/1135282295.svg)](https://doi.org/10.5281/zenodo.18475556)

</div>

tacular is a lookup library for the reference data every mass-spec/proteomics tool
needs: amino acids, elements and isotopes, and post-translational modification
ontologies (UNIMOD, PSI-MOD, RESID, XLMOD, GNOme, UniProt-PTM). It has no runtime
dependencies, so it's an easy way to add "what modification has a delta mass of
X" or "what's the monoisotopic mass of alanine" to any Python project. It's also
the shared data layer behind [peptacular](https://github.com/tacular-omics/peptacular)
(ProForma peptide sequences) and [paftacular](https://github.com/tacular-omics/paftacular)
(mzPAF fragment annotations).

## Why tacular?

- **Six PTM ontologies in one interface** — UNIMOD, PSI-MOD, RESID, XLMOD, GNOme,
  and UniProt-PTM, all queryable by id, name, or approximate mass.
- **Amino acid, element, ion-type, neutral-loss, protease, and mzPAF reference
  molecule lookups**, through the same simple `LOOKUP[key]` interface.
- **No runtime dependencies.**
- **Refreshable without reinstalling**: data ships baked into the package, and
  the `tacular update` CLI can pull the latest ontology release into a per-user
  cache on demand.
- **Typed** (`py.typed`) dataclasses for every entry.

## Install

```bash
pip install tacular
```

## Quick example

```python
import tacular as t

# Look up amino acids and elements by code or name
alanine = t.AA_LOOKUP["A"]
print(alanine.monoisotopic_mass)  # 71.0371137851

carbon_13 = t.ELEMENT_LOOKUP["13C"]
print(carbon_13.mass)  # 13.00335483507

# Identify a modification from an observed mass shift
hits = t.UNIMOD_LOOKUP.query_mass(79.9663, tolerance=0.001)
print(hits[0].name)  # Phospho
```

## What else it can do

- Query PSI-MOD, RESID, XLMOD, GNOme, and UniProt-PTM the same way as UNIMOD above.
- Look up fragment ion types, common neutral losses, mzPAF reference molecules,
  and protease cleavage patterns.
- Refresh any ontology to its latest upstream release without reinstalling:

  ```bash
  tacular update                 # refresh all pullable ontologies
  tacular update unimod xlmod    # refresh a subset (GNOme is a large download; opt in explicitly)
  tacular status                 # show bundled vs. cached versions
  tacular clear                  # revert to the bundled data
  ```

  The refresh takes effect on the next `import tacular`. See the
  [docs](https://tacular.readthedocs.io/) for the full CLI reference (including
  `--offline`, verbosity flags, and cache environment variables) and the complete
  lookup API.

## Documentation

- Full docs: [tacular.readthedocs.io](https://tacular.readthedocs.io/)
- Changelog: [CHANGELOG.md](https://github.com/tacular-omics/tacular/blob/main/CHANGELOG.md)
- Architecture and contributing (also useful for AI coding agents): [CLAUDE.md](https://github.com/tacular-omics/tacular/blob/main/CLAUDE.md)
  (`AGENTS.md` points here for tools that look for that filename instead)
- Data-generation pipeline (regenerating the bundled ontology snapshots): [data_gen/README.md](https://github.com/tacular-omics/tacular/blob/main/data_gen/README.md)

## Funding

Supported by NIH grants R01AG077046, R01MH132570, R01MH100175, R01HL165168 and U01AG088679.
