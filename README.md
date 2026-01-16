# tacular

Common utilities and data definitions for the tacular ecosystem, focused on mass spectrometry and proteomics.

## Features

`tacular` provides easy access to chemical and biological data including:

- **Periodic Table**: Access elements, isotopes, and calculate masses.
- **Amino Acids**: Data for standard amino acids.
- **Proteomics Ontologies**: Parsed and accessible data from major controlled vocabularies:
  - **Unimod** (Protein modifications)
  - **PSI-MOD** (Protein modifications)
  - **RESID** (Protein modifications)
  - **XLMOD** (Cross-linking reagents)
  - **GNO** (Glycan Naming Ontology)
- **Utilities**:
  - Proteases and cleavage rules
  - Fragment ion types
  - Monosaccharides
  - Reference molecules

## Installation

You can install `tacular` using `uv` or `pip`:

```bash
just install
# or
uv pip install .
```

## Development

This project uses `just` for task management.

```bash
just lint    # Run linters
just format  # Format code
just check   # Run type checking
just test    # Run tests
just gen     # Regenerate data files from source OBOs
```
