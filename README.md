# tacular

<div align="center">
  <img src="https://raw.githubusercontent.com/tacular-omics/tacular/main/tacular_logo.png" alt="tacular Logo" width="400" style="margin: 50px;"/>

  A Python library for looking up common MS-proteomics values. Includes the following modifications: UNIMOD, RESID, XLMOD, GNOme, PSIMOD, and UniProt-PTM. Also contains a lookup of elements, MS ion types, neutral deltas, proteases, and some reference molecules. Tacular is mainly a helper package for peptacular and paftacular.

    
[![Python package](https://github.com/pgarrett-scripps/tacular/actions/workflows/python-package.yml/badge.svg)](https://github.com/pgarrett-scripps/tacular/actions/workflows/python-package.yml)
[![codecov](https://codecov.io/github/tacular-omics/tacular/graph/badge.svg?token=1CTVZVFXF7)](https://codecov.io/github/tacular-omics/tacular)
[![Documentation Status](https://readthedocs.org/projects/tacular/badge/?version=latest)](https://tacular.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/tacular.svg)](https://badge.fury.io/py/tacular)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/1135282295.svg)](https://doi.org/10.5281/zenodo.18475556)

  
</div>

## Updating data from the latest ontologies

tacular ships with a snapshot of each ontology baked into the package. To refresh
to the latest releases without reinstalling, use the `tacular` CLI. It downloads
the current `.obo` sources, regenerates the data, and stores it in a per-user
cache that the lookups prefer over the bundled snapshot on the next import.

```bash
tacular update                 # refresh all pullable ontologies (UNIMOD, PSI-MOD, RESID, XLMOD, GNOme, UniProt-PTM)
tacular update unimod xlmod    # refresh a subset (GNOme is a large download; opt in explicitly)
tacular update --offline DIR   # regenerate from local .obo files in DIR (no network)
tacular status                 # show bundled vs cached versions
tacular clear                  # remove the cache and revert to the bundled data
tacular where                  # print the cache directory
tacular -vv update             # -v/-vv raise verbosity (info/debug); parsing failures always warn with a traceback
```

The refresh takes effect on the next `import tacular`. Environment variables:
`TACULAR_DATA_DIR` overrides the cache location; `TACULAR_DISABLE_CACHE=1` ignores
the cache and always uses the bundled data. Equivalent to the CLI: `python -m tacular ...`.

If an ontology release contains an entry `tacular` can't parse (or a cached file
gets corrupted), a warning is logged with the offending id/name, the raw input,
the exception type/message, and a full traceback — the root cause should be
diagnosable directly from the log without a debugger.

## Generate Data

See data_gen/README.md

## Generating JSONs

It's possible to generate JSON objects for all parsed data used within tacular. This isn't used within tacular or its downstream packages, but may be useful in other projects, especially those not Python-based. This will be created from the data within the python package, so ensure that this is up to date. See data_gen/README.md for more info. 

```bash
just gen-jsons
```

## Overview

The following lookups are available:

### Amino Acids
- Standard and non-standard amino acid lookups
- Query by single-letter code, three-letter code, or full name
- Access to molecular properties (mass, formula, etc.)

### Modifications
- Post-translational modifications (PTMs)
- Query by modification name, ID, or delta mass
- Support for Unimod, PSI-MOD, RESID, XLMOD, GNOme, and UniProt-PTM

### Elements
- Chemical element data
- Query by symbol, name
- Isotope information and masses

### Additional Data Types
- Fragment ions
- Common neutral deltas (mainly neutral losses)
- mzPAF reference molecules
- Common Proteases

## Architecture

Each lookup contains three core components:

- **data.py**: Auto-generated data file (should not be modified manually)
- **dclass.py**: Dataclass definitions for the data structures (subclass `OboEntity`, see `obo_entity.py`)
- **lookup.py**: Lookup implementation with query methods (subclass `OntologyLookup`, see `obo_lookup.py`)

Each lookup provides multiple query options to enable data retrieval by various means. Lookups are cached for faster repeat queries.

Two more pieces support the 6 ontologies that can be refreshed at runtime
(UNIMOD, PSI-MOD, RESID, XLMOD, GNOme -- all OBO-sourced -- and UniProt-PTM,
sourced from UniProt's own `ptmlist.txt` flat file) specifically:

- **`_datagen/`**: the parsing logic, one module per ontology. This is the
  single source of truth — both the developer generators (`data_gen/`) and the
  `tacular update` CLI call into it. See `data_gen/README.md`.
- **`_cache.py`**: resolves each lookup's data from a refreshed per-user cache
  if present, else the bundled `data.py` — see "Updating data from the latest
  ontologies" above.

## Usage

```python
import tacular as t

# Query amino acids
alanine = t.AA_LOOKUP['A']
carbon_13 = t.ELEMENT_LOOKUP['13C']
```

## Contributing / working with an AI agent

See [`CLAUDE.md`](CLAUDE.md) for an architecture and command reference aimed at
AI coding agents (also generally useful for new contributors); [`AGENTS.md`](AGENTS.md)
points here for tools that look for that filename instead.
