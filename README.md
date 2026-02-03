# tacular

<div align="center">
  <img src="tacular_logo.png" alt="tacular Logo" width="400" style="margin: 50px;"/>

  A Python library for looking up common MS-proteomics values. Includes the following modifications: UNIMOD, RESID, XLMOD, GNOme, and PSIMOD. Also contains a lookup of elements, MS ion types, neutral deltas, proteases, and soem reference molecules. Tacular is mainly a helper package for peptacular and paftacular.

    
[![Python package](https://github.com/pgarrett-scripps/tacular/actions/workflows/python-package.yml/badge.svg)](https://github.com/pgarrett-scripps/tacular/actions/workflows/python-package.yml)
[![codecov](https://codecov.io/github/tacular-omics/tacular/graph/badge.svg?token=1CTVZVFXF7)](https://codecov.io/github/tacular-omics/tacular)
[![Documentation Status](https://readthedocs.org/projects/tacular/badge/?version=latest)](https://tacular.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/tacular.svg)](https://badge.fury.io/py/tacular)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DOI](https://zenodo.org/badge/1135282295.svg)](https://doi.org/10.5281/zenodo.18475556)

  
</div>

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
- Support for Unimod, PSI-MOD, RESID, XLMOD and GNOme

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
- **dclass.py**: Dataclass definitions for the data structures
- **lookup.py**: Lookup implementation with query methods

Each lookup provides multiple query options to enable data retrieval by various means. Lookups are cached for faster repeat queries.

## Usage

```python
import tacular as t

# Query amino acids
alanine = t.AA_LOOKUP['A']
carbon_13 = t.ELEMENT_LOOKUP['13C']
```
